from ..paths import load_yaml

META_COLUMNS = {"record_id", load_yaml("data.yaml")["target_column"]}
FORBIDDEN_FEATURES = {"name", "first_name", "last_name", "student_name", "email", "phone", "address", "matricule"}

