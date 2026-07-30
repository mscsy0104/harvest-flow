import yaml

def parse_markdown(file_path):
    """마크다운 파일의 YAML 프론트매터와 본문을 분리하여 파싱"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_text = parts[1]
                body_text = parts[2]
                meta = yaml.safe_load(yaml_text)
                return meta, body_text, yaml_text
    except Exception as e:
        print(f"❌ 파싱 에러 ({file_path}): {e}")
    return None, None, None