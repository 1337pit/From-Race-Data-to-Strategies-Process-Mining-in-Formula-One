# From Race Data to Strategies: Process Mining in Formula One
Material used for the analysis conducted in the paper "From Race Data to Strategies: Process Mining in Formula One"

## Generating the event logs

The Python script downloads the lap data of a Grand Prix session through the [FastF1](https://docs.fastf1.dev) library, turns it into an event log (one row per event) and exports it as CSV.

### Requirements

- Python 3.8 or higher
- A recent version of [FastF1](https://docs.fastf1.dev) (the script uses `fastf1.Cache.configure`)
- [pandas](https://pandas.pydata.org/)

## Running the script

The session to download is set through the constants at the top of the script:

```python
YEAR = 2025
GRAND_PRIX = "British Grand Prix"
SESSION_TYPE = "R"
OUTPUT_DIR = Path("silverstone_2025")
```

| Constant | Description | Example |
|----------|-------------|---------|
| `YEAR` | Season year | `2025` |
| `GRAND_PRIX` | Grand Prix name as understood by FastF1 (or round number) | `"British Grand Prix"` |
| `SESSION_TYPE` | Session identifier: `FP1`, `FP2`, `FP3`, `Q`, `S`, `SQ`, `R` | `"R"` (race) |
| `OUTPUT_DIR` | Folder where cache and CSV files are written | `Path("silverstone_2025")` |

The command to run the script is:
```bash
python Python/pythonScript.py
```
