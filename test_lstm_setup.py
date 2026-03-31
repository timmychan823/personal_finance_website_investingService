"""
LSTM Stock Predictor - Setup Validation Script

This script verifies that all components are correctly set up:
- Model file exists and can be loaded
- Database connection works
- Required packages are installed
- Sample ticker can be predicted
"""

import sys
import os
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(text):
    """Print section header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_status(item, status, message=""):
    """Print status of a check"""
    symbol = "✓" if status else "✗"
    status_text = "OK" if status else "FAILED"
    print(f"  [{symbol}] {item:<40} {status_text}")
    if message:
        print(f"      {message}")


def check_python_version():
    """Check Python version"""
    print_header("Python Version Check")
    version = sys.version_info
    required = (3, 8)
    status = version >= required
    print_status(
        f"Python {version.major}.{version.minor}",
        status,
        f"Required: {required[0]}.{required[1]}+" if not status else ""
    )
    return status


def check_package_imports():
    """Check if required packages can be imported"""
    print_header("Required Packages Check")
    
    packages = {
        'numpy': 'Numerical operations',
        'pandas': 'Data manipulation',
        'tensorflow': 'LSTM model loading',
        'yfinance': 'Stock data retrieval',
        'ta': 'Technical indicators',
        'psycopg2': 'PostgreSQL connection',
        'sklearn': 'Scikit-learn utilities',
    }
    
    all_ok = True
    for package, description in packages.items():
        try:
            __import__(package)
            print_status(f"{package:<20} {description}", True)
        except ImportError:
            print_status(f"{package:<20} {description}", False, "Not installed")
            all_ok = False
    
    return all_ok


def check_model_file():
    """Check if model file exists"""
    print_header("Model File Check")
    
    model_path = Path('./lstmModel/fypLSTM.h5')
    exists = model_path.exists()
    print_status(
        f"Model file: {model_path}",
        exists,
        f"Size: {model_path.stat().st_size / (1024*1024):.1f}MB" if exists else "File not found"
    )
    
    if exists:
        try:
            from lstm_stock_predictor import LSTMStockPredictor
            predictor = LSTMStockPredictor(str(model_path))
            print_status("Model loading", True, "Successfully loaded into memory")
            return True
        except Exception as e:
            print_status("Model loading", False, str(e))
            return False
    
    return False


def check_database_connection():
    """Check database connectivity"""
    print_header("Database Connection Check")
    
    try:
        import psycopg2
        from src.constant.Db_constants import DB_USER, DB_PW, DB_HOST, DB_PORT, DB_NAME
        
        pg_connection_dict = {
            'dbname': DB_NAME,
            'user': DB_USER,
            'password': DB_PW,
            'port': DB_PORT,
            'host': DB_HOST
        }
        
        logger.info(f"Attempting connection to {DB_HOST}:{DB_PORT}/{DB_NAME}...")
        conn = psycopg2.connect(**pg_connection_dict)
        conn.close()
        print_status("Database connection", True, f"{DB_HOST}:{DB_PORT}/{DB_NAME}")
        return True
    
    except Exception as e:
        print_status("Database connection", False, str(e))
        return False


def check_tickers_in_database():
    """Check if tickers exist in database"""
    print_header("Database Content Check")
    
    try:
        from src.constant.Db_constants import DB_USER, DB_PW, DB_HOST, DB_PORT, DB_NAME, COMPANY_TABLE_NAME
        import psycopg2
        
        pg_connection_dict = {
            'dbname': DB_NAME,
            'user': DB_USER,
            'password': DB_PW,
            'port': DB_PORT,
            'host': DB_HOST
        }
        
        conn = psycopg2.connect(**pg_connection_dict)
        
        with conn.cursor() as curs:
            query = f'SELECT COUNT(*) FROM public."{COMPANY_TABLE_NAME}"'
            curs.execute(query)
            count = curs.fetchone()[0]
            print_status(f"Tickers in {COMPANY_TABLE_NAME}", count > 0, f"Found {count} tickers")
            
            if count > 0:
                query = f'SELECT ticker FROM public."{COMPANY_TABLE_NAME}" LIMIT 5'
                curs.execute(query)
                tickers = [row[0] for row in curs.fetchall()]
                print_status("Sample tickers", True, ", ".join(tickers))
        
        conn.close()
        return count > 0
    
    except Exception as e:
        print_status("Tickers query", False, str(e))
        return False


def test_sample_prediction():
    """Test prediction with a sample ticker"""
    print_header("Sample Prediction Test")
    
    try:
        from lstm_stock_predictor import LSTMStockPredictor
        
        logger.info("Loading model...")
        predictor = LSTMStockPredictor('./lstmModel/fypLSTM.h5')
        
        logger.info("Testing prediction with TSLA...")
        result = predictor.predict('TSLA')
        
        if result['status'] == 'success':
            prediction_text = "UP ↑" if result['prediction'] == 1 else "DOWN ↓"
            print_status(
                "TSLA prediction",
                True,
                f"{prediction_text} with {result['confidence']:.2%} confidence"
            )
            return True
        else:
            print_status("TSLA prediction", False, result['message'])
            return False
    
    except Exception as e:
        print_status("Sample prediction", False, str(e))
        return False


def main():
    """Run all validation checks"""
    print("\n" + "=" * 70)
    print("  LSTM STOCK PREDICTOR - SETUP VALIDATION")
    print("=" * 70)
    
    results = {}
    
    # Run all checks
    results['Python Version'] = check_python_version()
    results['Required Packages'] = check_package_imports()
    results['Model File'] = check_model_file()
    results['Database Connection'] = check_database_connection()
    results['Database Content'] = check_tickers_in_database()
    results['Sample Prediction'] = test_sample_prediction()
    
    # Summary
    print_header("Validation Summary")
    
    all_passed = True
    for check, result in results.items():
        symbol = "✓" if result else "✗"
        status = "PASSED" if result else "FAILED"
        print(f"  [{symbol}] {check:<40} {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 70)
    
    if all_passed:
        print("  ✓ All checks passed! System is ready for predictions.")
        print("\n  You can now run predictions using:")
        print("    python lstm_predictor_util.py --all")
        print("    python lstm_predictor_util.py --tickers TSLA AAPL MSFT")
        print("    python lstm_predictor_util.py --all --save")
    else:
        print("  ✗ Some checks failed. Please fix the issues above.")
        print("\n  Troubleshooting:")
        print("    - Install missing packages: pip install -r requirements.txt")
        print("    - Check database connection settings in src/constant/Db_constants.py")
        print("    - Ensure model file exists at lstmModel/fypLSTM.h5")
        print("    - Check database is running and accessible")
    
    print("=" * 70 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
