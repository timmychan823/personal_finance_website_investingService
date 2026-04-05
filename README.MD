Please run all CREATE statement in usefulSQL.sql to create databases and tables
and run all ALTER statement in usefulSQL.sql to change owner before starting the application
create python virtual environment:
python -m venv venv
./venv/Scripts/activate
pip install -r requirements.txt
Please add a chrome driver to the project root directory for selenium to use it.
Please create a model folder under the project root directory and run git clone https://huggingface.co/ProsusAI/finbert in the model folder created.
Add a windows scheduled task in the server to run the script using the following command: powershell.exe -file {path to root of this project}/newsProcessing.ps1
Add a windows scheduled task in the server to run the script using the following command: powershell.exe -file {path to root of this project}/stockPrediction.ps1