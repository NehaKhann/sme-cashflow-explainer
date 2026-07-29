from datasets import load_dataset, get_dataset_config_names

configs = get_dataset_config_names("AdaptLLM/finance-tasks")
print("Configs:", configs)

for cfg in configs:
    ds = load_dataset("AdaptLLM/finance-tasks", cfg, split="test")
    sample = ds[0]
    print(f"\n{cfg}: columns={ds.column_names}")
    for k, v in sample.items():
        print(f"  {k}: {str(v)[:120]}")
