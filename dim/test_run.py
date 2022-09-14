import yaml 
path = "test_config.yml"
with open(path, "r") as f:
    config = yaml.safe_load(f)

print(config)