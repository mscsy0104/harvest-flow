import time
from pathlib import Path
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler

from src.parser import parse_markdown
from src.database import (
    init_infrastructure,
    update_metadata_db,
    save_to_vector_db,
    list_tracked_note_filenames,
    list_ready_to_publish,
    update_workflow_stage,
    mark_manual_review,
    schedule_publish,
    set_post_id,
    get_note_metadata,
    schedule_delete_request,
    cancel_delete_request,
    mark_delete_done,
    mark_delete_failed,
    list_ready_to_delete,
    delete_note_from_metadata_db,
    delete_note_from_vector_db,
)
from src.agent_pipeline import generate_ai_metadata
from src.utils import (
    calculate_file_hash,
    is_already_cached,
    update_file_cache,
    delete_file_cache_entry,
    list_cached_file_paths,
    generate_compact_id,
    get_file_created_ts,
    format_ts,
    now_iso,
    publish_content,
    unpublish_content,
)
from src.logger import logger
from src.workflow import (
    STAGE_DRAFT,
    STAGE_REVIEW_REQUEST,
    STAGE_PUBLISH_WAIT,
    STAGE_NEEDS_FIX,
    STAGE_SECOND_REVIEW_DONE,
    STAGE_PUBLISHED,
    STAGE_REVISE_WAIT,
    STAGE_DELETE_REQUEST,
    STAGE_TRASH,
    clear_manual_review_flag,
    ensure_review_checklist,
    generate_post_id,
    is_workflow_file,
    list_workflow_files,
    manual_review_passed,
    move_note_to_stage,
    run_first_review,
    set_frontmatter_fields,
    stage_from_path,
    WORKFLOW_STAGE_DIRS,
)
from config import (
    NOTES_DIR,
    PUBLISH_CONTENT_DIR,
    VECTOR_DB_CLIENT,
    PUBLISH_CLIENT,
    STARTUP_SYNC,
    PUBLISH_DELAY_MINUTES,
    DELETE_DELAY_MINUTES,
)


def pipeline_trigger(file_path: str) -> bool:
    """출간 노트면 파이프라인을 돌리고, 실제 처리 여부를 반환합니다."""
    path = Path(file_path)
    filename = path.name

    meta, body_text, yaml_text = parse_markdown(file_path)
    if not (meta and meta.get("status") == "출간"):
        return False

    mtime = path.stat().st_mtime
    compact_id = generate_compact_id(file_path)
    created_at = format_ts(get_file_created_ts(file_path))
    logger.info("파이프라인 가동: %s (id=%s)", filename, compact_id)

    ai_refined = generate_ai_metadata(body_text)
    ai_processed_at = now_iso()

    processed_content = (
        "---\n"
        f"{yaml_text.strip()}\n"
        "---\n\n"
        f"### 🤖 AI 자동 요약 및 인덱싱\n"
        f"{ai_refined.strip()}\n\n"
        "---\n\n"
        f"### 본문\n"
        f"{body_text.strip()}"
    )

    publish_content_path = PUBLISH_CONTENT_DIR / filename
    with publish_content_path.open("w", encoding="utf-8") as file:
        file.write(processed_content)
    published_at = now_iso()

    update_metadata_db(filename, mtime, "출간")
    vector_payload = {
        "title": filename,
        "status": "출간",
        "post_id": str(meta.get("post_id", "")).strip() or None,
        "compact_id": compact_id,
        "created_at": created_at,
        "ai_processed_at": ai_processed_at,
        "published_at": published_at,
        "ai_summary_and_tags": ai_refined.strip(),
    }
    save_to_vector_db(filename, body_text, vector_payload)
    logger.info(
        "엔드투엔드 완료 (publish=%s · vector=%s): %s",
        PUBLISH_CLIENT,
        VECTOR_DB_CLIENT,
        filename,
    )

    # 설정된 publish client를 통해 출하를 실행합니다.
    publish_content(filename)
    return True


def _now_ts() -> float:
    return time.time()


def cleanup_note_artifacts(file_path: str) -> None:
    """노트 삭제/이동 시 메타·벡터·캐시·출하 파일을 정리합니다."""
    filename = Path(file_path).name
    delete_note_from_metadata_db(filename)
    delete_note_from_vector_db(filename)
    delete_file_cache_entry(file_path)

    publish_content_path = PUBLISH_CONTENT_DIR / filename
    try:
        if publish_content_path.exists():
            publish_content_path.unlink()
    except Exception:
        logger.exception("출하 파일 정리 실패: %s", publish_content_path)

    logger.info("삭제/이동 정리 완료: %s", filename)


def cleanup_removed_notes_at_startup(note_files: list[Path]) -> None:
    """시작 시 현재 파일 목록 기준으로 삭제/이동된 흔적을 정리합니다."""
    current_filenames = {path.name for path in note_files}
    tracked_filenames = list_tracked_note_filenames()
    stale_filenames = sorted(tracked_filenames - current_filenames)

    for stale_name in stale_filenames:
        cleanup_note_artifacts(str(NOTES_DIR / stale_name))

    current_paths = {str(path) for path in note_files}
    stale_cache_paths = []
    notes_dir_prefix = str(NOTES_DIR.resolve())
    for cached_path in list_cached_file_paths():
        path_obj = Path(cached_path)
        if not path_obj.is_absolute():
            continue
        if not str(path_obj).startswith(notes_dir_prefix):
            continue
        if cached_path not in current_paths:
            stale_cache_paths.append(cached_path)

    for cached_path in stale_cache_paths:
        delete_file_cache_entry(cached_path)

    if stale_filenames or stale_cache_paths:
        logger.info(
            "startup 정리 완료: metadata/vector=%d건, file_cache=%d건",
            len(stale_filenames),
            len(stale_cache_paths),
        )


def sync_metadata_for_stage(file_path: str, stage: str) -> None:
    path = Path(file_path)
    if not path.exists():
        return
    status = "출간" if stage == STAGE_PUBLISHED else stage
    update_metadata_db(
        path.name,
        path.stat().st_mtime,
        status,
        workflow_stage=stage,
        last_transition_at=_now_ts(),
    )


def _send_to_stage(file_path: str, target_stage: str) -> str:
    moved = move_note_to_stage(file_path, target_stage)
    sync_metadata_for_stage(str(moved), target_stage)
    return str(moved)


def handle_review_request(file_path: str) -> str:
    ensure_review_checklist(file_path, reset_existing=True)
    # 1차 자동 검수 임시 비활성화:
    # passed, reasons = run_first_review(file_path)
    # if passed:
    #     clear_manual_review_flag(file_path)
    #     moved_path = _send_to_stage(file_path, STAGE_PUBLISH_WAIT)
    #     mark_manual_review(Path(moved_path).name, False, transition_ts=_now_ts())
    #     logger.info("1차 자동 검수 통과 → %s", moved_path)
    #     return moved_path
    #
    # moved_path = _send_to_stage(file_path, STAGE_NEEDS_FIX)
    # logger.info("1차 자동 검수 실패(%s) → %s", " / ".join(reasons), moved_path)
    clear_manual_review_flag(file_path)
    moved_path = _send_to_stage(file_path, STAGE_PUBLISH_WAIT)
    mark_manual_review(Path(moved_path).name, False, transition_ts=_now_ts())
    logger.info("1차 자동 검수 비활성화 상태: 출간대기로 이동 → %s", moved_path)
    return moved_path


def handle_publish_wait(file_path: str) -> str:
    if not manual_review_passed(file_path):
        sync_metadata_for_stage(file_path, STAGE_PUBLISH_WAIT)
        return file_path

    clear_manual_review_flag(file_path)
    moved_path = _send_to_stage(file_path, STAGE_SECOND_REVIEW_DONE)
    ready_at = _now_ts() + (PUBLISH_DELAY_MINUTES * 60)
    mark_manual_review(Path(moved_path).name, True, transition_ts=_now_ts())
    schedule_publish(Path(moved_path).name, ready_at, transition_ts=_now_ts())
    logger.info("수동 검수 승인 감지 → 2차검수완료 이동: %s", moved_path)
    return moved_path


def handle_revise_wait(file_path: str) -> str:
    moved_path = _send_to_stage(file_path, STAGE_REVIEW_REQUEST)
    logger.info("수정대기 진입 감지 → 검수요청 재진입: %s", moved_path)
    return moved_path


def handle_second_review_done_entry(file_path: str) -> str:
    """2차검수완료 폴더 직접 진입 시에도 출간 예약을 설정합니다."""
    sync_metadata_for_stage(file_path, STAGE_SECOND_REVIEW_DONE)
    filename = Path(file_path).name
    meta = get_note_metadata(filename) or {}
    ready_for_publish_at = meta.get("ready_for_publish_at")

    if ready_for_publish_at:
        return file_path

    now_ts = _now_ts()
    ready_at = now_ts + (PUBLISH_DELAY_MINUTES * 60)
    mark_manual_review(filename, True, transition_ts=now_ts)
    schedule_publish(filename, ready_at, transition_ts=now_ts)
    logger.info(
        "2차검수완료 진입 감지 → 출간 예약 설정: %s (due in %d min)",
        file_path,
        PUBLISH_DELAY_MINUTES,
    )
    return file_path


def maybe_cancel_pending_delete(filename: str, stage: str) -> None:
    """삭제요청 외 단계로 이동되면 대기중 삭제 요청을 취소합니다."""
    if stage == STAGE_DELETE_REQUEST:
        return
    meta = get_note_metadata(filename)
    if not meta:
        return
    delete_status = str(meta.get("delete_status") or "")
    if delete_status not in {"requested", "failed"}:
        return
    cancel_delete_request(
        filename,
        cancelled_at=_now_ts(),
        reason=f"stage changed to {stage}",
        transition_ts=_now_ts(),
    )
    logger.info("삭제 요청 취소: %s (stage=%s)", filename, stage)


def handle_delete_request(file_path: str) -> str:
    """삭제요청 단계 진입 시 지연 삭제 타이머를 설정합니다."""
    sync_metadata_for_stage(file_path, STAGE_DELETE_REQUEST)
    filename = Path(file_path).name
    meta = get_note_metadata(filename) or {}
    delete_status = str(meta.get("delete_status") or "")
    delete_due_at = meta.get("delete_due_at")
    if delete_status == "requested" and delete_due_at:
        return file_path

    requested_at = _now_ts()
    due_at = requested_at + (DELETE_DELAY_MINUTES * 60)
    schedule_delete_request(
        filename,
        requested_at=requested_at,
        due_at=due_at,
        transition_ts=requested_at,
    )
    logger.info("삭제 요청 접수: %s (due in %d min)", filename, DELETE_DELAY_MINUTES)
    return file_path


def handle_soft_delete(file_path: str) -> bool:
    """삭제 API 호출 + 휴지통 이동을 수행합니다."""
    path = Path(file_path)
    if not path.exists():
        return False

    filename = path.name
    if not unpublish_content(filename):
        mark_delete_failed(
            filename,
            error_text="unpublish_content returned false",
            transition_ts=_now_ts(),
        )
        return False

    moved_path = _send_to_stage(str(path), STAGE_TRASH)
    now_ts = _now_ts()
    mark_delete_done(Path(moved_path).name, completed_at=now_ts, transition_ts=now_ts)
    update_workflow_stage(
        Path(moved_path).name,
        STAGE_TRASH,
        transition_ts=now_ts,
    )
    logger.info("soft 삭제 완료 → 휴지통 이동: %s", moved_path)
    return True


def handle_second_review_publish(file_path: str) -> bool:
    path = Path(file_path)
    if not path.exists():
        return False

    post_id = generate_post_id(file_path)
    set_frontmatter_fields(path, status="출간", post_id=post_id)
    processed = pipeline_trigger(str(path))
    if not processed:
        logger.warning("출간 파이프라인 스킵(status 미일치): %s", path.name)
        return False

    moved_path = _send_to_stage(str(path), STAGE_PUBLISHED)
    set_post_id(Path(moved_path).name, post_id, transition_ts=_now_ts())
    update_workflow_stage(
        Path(moved_path).name,
        STAGE_PUBLISHED,
        manual_review_passed=True,
        ready_for_publish_at=None,
        post_id=post_id,
        transition_ts=_now_ts(),
    )
    logger.info("자동 출간 완료(post_id=%s) → %s", post_id, moved_path)
    return True


def process_workflow_file(file_path: str, *, force: bool = False) -> str:
    if not is_workflow_file(file_path):
        return file_path

    path = Path(file_path)
    if not path.exists():
        return file_path

    stage = stage_from_path(path)
    if stage is None:
        return file_path

    maybe_cancel_pending_delete(path.name, stage)

    if stage == STAGE_REVIEW_REQUEST:
        return handle_review_request(str(path))
    if stage == STAGE_PUBLISH_WAIT:
        return handle_publish_wait(str(path))
    if stage == STAGE_REVISE_WAIT:
        return handle_revise_wait(str(path))
    if stage == STAGE_DELETE_REQUEST:
        return handle_delete_request(str(path))
    if stage == STAGE_TRASH:
        sync_metadata_for_stage(str(path), stage)
        return str(path)
    if stage == STAGE_SECOND_REVIEW_DONE:
        return handle_second_review_done_entry(str(path))

    sync_metadata_for_stage(str(path), stage)
    return str(path)


def should_skip_cached_event(stage: str | None) -> bool:
    """단순 중복 이벤트는 캐시로 막되, 전이 핵심 단계는 항상 재처리합니다."""
    # 아래 단계들은 "폴더 이동 자체"가 트리거이므로 동일 해시여도 처리해야 합니다.
    return stage not in {
        STAGE_REVIEW_REQUEST,
        STAGE_PUBLISH_WAIT,
        STAGE_REVISE_WAIT,
        STAGE_DELETE_REQUEST,
        STAGE_SECOND_REVIEW_DONE,
    }


def process_due_publications() -> None:
    due_rows = list_ready_to_publish(_now_ts(), stage_name=STAGE_SECOND_REVIEW_DONE)
    if not due_rows:
        return

    for row in due_rows:
        filename = row["filename"]
        path = WORKFLOW_STAGE_DIRS[STAGE_SECOND_REVIEW_DONE] / filename
        if not path.exists():
            continue
        try:
            handle_second_review_publish(str(path))
        except Exception:
            logger.exception("지연 출간 처리 실패: %s", filename)
            # 즉시 무한 재시도로 Ollama를 압박하지 않도록 다음 재시도를 잠시 지연합니다.
            retry_at = _now_ts() + 60
            schedule_publish(filename, retry_at, transition_ts=_now_ts())
            logger.info("지연 출간 재시도 예약: %s (due in 1 min)", filename)


def process_due_deletions() -> None:
    due_rows = list_ready_to_delete(_now_ts(), stage_name=STAGE_DELETE_REQUEST)
    if not due_rows:
        return

    for row in due_rows:
        filename = row["filename"]
        path = WORKFLOW_STAGE_DIRS[STAGE_DELETE_REQUEST] / filename
        if not path.exists():
            cancel_delete_request(
                filename,
                cancelled_at=_now_ts(),
                reason="file missing in delete-request stage",
                transition_ts=_now_ts(),
            )
            continue

        try:
            handle_soft_delete(str(path))
        except Exception as exc:
            logger.exception("지연 삭제 처리 실패: %s", filename)
            mark_delete_failed(
                filename,
                error_text=str(exc),
                transition_ts=_now_ts(),
            )


def run_startup_sync() -> None:
    """앱 시작 시 워크플로우 상태를 1회 동기화합니다."""
    if not STARTUP_SYNC:
        logger.info("startup sync 비활성화(APP_STARTUP_SYNC=0)")
        return

    note_files = list_workflow_files()
    if not note_files:
        logger.info("startup sync 대상 없음: workflow stage directories")
        return

    logger.info("workflow startup sync 시작: %d개 노트", len(note_files))
    for note_file in note_files:
        file_path = str(note_file)
        stage = stage_from_path(note_file)
        current_hash = calculate_file_hash(file_path)
        if is_already_cached(file_path, current_hash) and should_skip_cached_event(stage):
            continue

        try:
            final_path = process_workflow_file(file_path, force=True)
            final_hash = calculate_file_hash(final_path)
            update_file_cache(final_path, final_hash)
        except Exception:
            logger.exception("startup workflow 처리 실패: %s", file_path)

    process_due_publications()
    process_due_deletions()
    logger.info("workflow startup sync 완료")


class NotesHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith(".md"):
            return

        self._handle_markdown_modified(event.src_path)

    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".md"):
            return
        self._handle_markdown_modified(event.src_path)

    def on_deleted(self, event):
        if event.is_directory or not event.src_path.endswith(".md"):
            return
        self._handle_markdown_deleted(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            return

        src_md = event.src_path.endswith(".md")
        dest_md = event.dest_path.endswith(".md")

        if src_md and dest_md:
            delete_file_cache_entry(event.src_path)
            # 동일 파일명이 과거에 같은 목적지 경로에 캐시된 경우를 제거합니다.
            delete_file_cache_entry(event.dest_path)
            self._handle_markdown_modified(event.dest_path)
            return

        if src_md:
            self._handle_markdown_deleted(event.src_path)
        if dest_md:
            self._handle_markdown_modified(event.dest_path)

    def _handle_markdown_modified(self, file_path: str) -> None:
        time.sleep(0.5)
        if not is_workflow_file(file_path):
            return

        stage = stage_from_path(file_path)
        current_hash = calculate_file_hash(file_path)
        if is_already_cached(file_path, current_hash) and should_skip_cached_event(stage):
            logger.info("캐시 존재, 워크플로우 처리 생략: %s", file_path)
            return

        try:
            final_path = process_workflow_file(file_path)
            final_hash = calculate_file_hash(final_path)
            update_file_cache(final_path, final_hash)
        except Exception:
            logger.exception("워크플로우 처리 실패: %s", file_path)

    def _handle_markdown_deleted(self, file_path: str) -> None:
        if not str(file_path).startswith(str(NOTES_DIR)):
            return
        try:
            cleanup_note_artifacts(file_path)
        except Exception:
            logger.exception("삭제/이동 정리 실패: %s", file_path)


if __name__ == "__main__":
    init_infrastructure()
    startup_note_files = list_workflow_files() if NOTES_DIR.exists() else []
    cleanup_removed_notes_at_startup(startup_note_files)
    run_startup_sync()
    logger.info("워크플로우 엔진 가동 중... (%s)", NOTES_DIR)

    event_handler = NotesHandler()
    observer = PollingObserver()
    # recursive = True: 워크플로우 하위 폴더 전체를 감시합니다.
    observer.schedule(event_handler, path=NOTES_DIR, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
            process_due_publications()
            process_due_deletions()
    except KeyboardInterrupt:
        logger.info("사용자 요청으로 종료 신호를 수신했습니다.")
    finally:
        observer.stop()
        observer.join()

        from src.database import get_vector_db_client

        try:
            vector_db_client = get_vector_db_client()
            vector_db_client.close()
            logger.info("%s vector DB 클라이언트가 안전하게 닫혔습니다.", VECTOR_DB_CLIENT)
        except Exception:
            logger.debug("종료 시 Qdrant close 생략 또는 실패", exc_info=True)

        logger.info("파이프라인 엔진이 정리되어 종료되었습니다.")
