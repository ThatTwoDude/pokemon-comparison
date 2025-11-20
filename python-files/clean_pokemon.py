import pandas as pd

df = pd.read_csv("data/raw/pokemon_raw.csv")

# Clean names
df["name"] = df["name"].str.title()

# Replace None with "None" for type2
df["type2"] = df["type2"].fillna("None")

# Save cleaned version
df.to_csv("data/clean/pokemon_clean.csv", index=False)

print("Saved cleaned dataset at data/clean/pokemon_clean.csv")