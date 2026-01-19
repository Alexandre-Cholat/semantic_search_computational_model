# semantic_search_computational_model

Computational modeling and data pipeline for studying lexical search patterns in a dictionary context. This repository contains an interactive interface to collect behavioral data and a simulation framework to evaluate computational models of human search strategies. A detailled description of the model, data collection, and methodology is available in the "Rapport Modélisation Computationnelle" document.

## Key ideas
- Provide an interactive environment to collect participant interaction data.
- Provide a pipeline to process collected data.
- Calibrate models using human baseline data.
- Utilize variables like word frequency (lexical retrieval cost) and polarization (alphabetical distance/position) to predict total search time.
- Make it easy for contributors to run experiments locally and help improve the model.

## How it works (high level)
1. Run the interactive experiment (experimental_environment/interface.py) locally to produce interaction logs. After each run, experimental data is automatically uploaded to a PostgreSQL cloud database.
2. Collected interactions are processed by the repository's data pipeline into anonymized, aggregated datasets. Data processing and model training workflows download the required experimental data from the PostgreSQL cloud database to a local or cloud processing environment.
3. Processed data is used to analyze behavior and to train computational models that aim to reproduce human semantic search patterns.

## Contributing

Anyone can contribute to the model by cloning the repo and trying the experience for themselves!

Minimal steps to get started:

1. git clone https://github.com/Alexandre-Cholat/semantic_search_computational_model.git
2. cd semantic_search_computational_model
3. python -m venv .venv  # or use your preferred virtualenv tool
   - On macOS/Linux: source .venv/bin/activate
   - On Windows (PowerShell): .\.venv\Scripts\Activate.ps1
4. pip install -r requirements.txt
5. Run the interactive/demo script: python experimental_environment/interface.py


The data collected from these runs will be used to train and improve the computational model. Data is inherently anonymized before being used for research or model training; by trying the experience you help improve the model. By participating you consent to the use of your interaction data for research and model training purposes.

## Funding and Acknowledgements
This work was supported by the French government, under the management of the National Research Agency (ANR), as part of the "Investments for the Future" program with the reference ANR-22-CMAS-0005.
