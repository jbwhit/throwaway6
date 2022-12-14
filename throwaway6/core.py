# AUTOGENERATED! DO NOT EDIT! File to edit: ../00_core.ipynb.

# %% auto 0
__all__ = ['app', 'cache_data', 'sample_from_spreadsheet']

# %% ../00_core.ipynb 3
import os
from pathlib import Path
import hashlib
import textwrap
from glob import glob

import pandas as pd
import typer
from rich import print
from rich.console import Console
from rich.markdown import Markdown
from rich.progress import wrap_file
from rich.table import Table

pd.set_option("display.max_colwidth", 1000)
pd.set_option("display.max_rows", 30)
app = typer.Typer()

# %% ../00_core.ipynb 5
def cache_data(
    url:str = "",
    force:bool = False,
    timedelta=pd.Timedelta(.5, unit='hour'),
    cache:bool = True,
    cleanup:bool = True,
    cache_location:str = "~/.cache/sampler",
    keeplast:int = 5,
):
    """Checks if the data exists or if the force is turned on. Returns """
    
    # Check cache location, if not exists create it.
    cache_location = cache_location.rstrip('/')
    cache_path = Path(os.path.expanduser(cache_location))
    if not cache_path.is_dir():
        Path(cache_path).mkdir(parents=True, exist_ok=True)
    
    # Look at the URL format a few options
    first = url.split("#")[0]
    sheet_id = url.split("/d/")[1].split("/")[0]
    long_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"

    # Create unique id for the URL
    slug = hashlib.md5(first.encode('utf-8')).hexdigest()
    # Create list of files (reverse sorted by time) that have the unique id for the URL
    files = sorted(glob(f"{cache_path}/*_{slug}.parquet"), reverse=True)
    
    timed_out = True
    now = pd.Timestamp('now')
    if len(files) > 0:
        file = files[0]
        time_last_cache = pd.to_datetime(file.split('/')[-1].split('_')[0], format="%Y-%m-%dT%H:%M:%S:%f")
        timed_out = (now - time_last_cache) > timedelta
    
    new_file = False
    if force or timed_out:
        df = pd.read_csv(long_url)
        new_file = True
    else:
        df = pd.read_parquet(file)
    if "weight" not in df.columns:
        df["weight"] = 1.0
    df["weight"] = df["weight"].fillna(1.0)
    if cache and new_file:
        df.to_parquet(f"{cache_path}/{now.strftime('%Y-%m-%dT%H:%M:%S:%f')}_{slug}.parquet")
    if cleanup:
        for file in files[keeplast:]:
            os.remove(file)
    return df

# %% ../00_core.ipynb 6
@app.command()
def sample_from_spreadsheet(
    url: str = "https://docs.google.com/spreadsheets/d/1F3-gMc8J57UBUo2DTsvVU7C1U1uncEpXmzE13DKwGQQ/edit#gid=1444336398",
    n_samples: int = 10,
    title: str = "",
    row_spacing: int = 5,
    first_n_columns: int = 1,
):
    console = Console()
    with console.status(
        "[bold green]Getting the data...", spinner="aesthetic"
    ) as status:
        df = cache_data(
                url=url,
             )

    ex = df.sample(n_samples, weights=df["weight"])
    table = Table(title=title)

    columns = df.columns
    for col in columns[:first_n_columns]:
        table.add_column(col, justify="left", style="cyan", no_wrap=False)
    # table.add_column("Year", justify="center", style="magenta")

    for index, (i, row) in enumerate(ex.iterrows(), start=1):
        full_row = [row[col] for col in columns[:first_n_columns]]
        # table.add_row(row[df.columns[0]])
        table.add_row(*full_row)
        if (index % row_spacing == 0) & (index < len(ex)) & (row_spacing > 0):
            table.add_row()

    md = Markdown(f"[Link to spreadsheet]({url})")
    table.caption = md
    print()
    print()
    console.print(table)
    print()
    print()


# if __name__ == "__main__":
#     app()
