import pandas as pd

df = pd.read_csv('./output/transcript_links.csv')

# Explode the transcript links by ;

df['Transcript Links'] = df['Transcript Links'].str.split(';')

df = df.explode('Transcript Links')

# Save the exploded transcript links to a new csv file
df.to_csv('./output/exploded_transcript_links.csv', index=False)

print('Exploded transcript links saved to ./output/exploded_transcript_links.csv')