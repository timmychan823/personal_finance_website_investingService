"""
LSTM Stock Predictor Utility Script

This script provides command-line interface to run stock predictions
and save them to the database.

Usage:
    # Predict for all tickers in database
    python lstm_predictor_util.py --all
    
    # Predict for specific tickers
    python lstm_predictor_util.py --tickers TSLA AAPL MSFT
    
    # Predict for all and save to database
    python lstm_predictor_util.py --all --save
    
    # Predict single ticker and display confidence scores
    python lstm_predictor_util.py --tickers TSLA --verbose
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from lstm_stock_predictor import LSTMStockPredictor, DatabaseManager
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def export_results(results: list, output_file: str = None):
    """
    Export prediction results to JSON file
    
    Args:
        results: List of prediction results
        output_file: Path to output file (optional)
    """
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"predictions_{timestamp}.json"
    
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results exported to {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"Error exporting results: {str(e)}")
        return None


def display_results(results: list, verbose: bool = False):
    """
    Display prediction results in formatted output
    
    Args:
        results: List of prediction results
        verbose: If True, show detailed information
    """
    print("\n" + "=" * 80)
    print("STOCK PRICE PREDICTION RESULTS")
    print("=" * 80)
    
    successful = []
    failed = []
    
    for result in results:
        if result['status'] == 'success':
            successful.append(result)
        else:
            failed.append(result)
    
    # Display successful predictions
    if successful:
        print(f"\n✓ SUCCESSFUL PREDICTIONS ({len(successful)}/{len(results)})")
        print("-" * 80)
        print(f"{'Ticker':<10} {'Prediction':<15} {'Confidence':<15} {'Date':<20}")
        print("-" * 80)
        
        for result in successful:
            prediction_text = "UP ↑" if result['prediction'] == 1 else "DOWN ↓"
            confidence_text = f"{result['confidence']:.2%}"
            print(f"{result['ticker']:<10} {prediction_text:<15} {confidence_text:<15} {str(result['prediction_date']):<20}")
        
        if verbose:
            print("\nDetailed Information:")
            for result in successful:
                print(f"\n  {result['ticker']}:")
                print(f"    Prediction: {'UP ↑' if result['prediction'] == 1 else 'DOWN ↓'}")
                print(f"    Confidence: {result['confidence']:.4f}")
                print(f"    Message: {result['message']}")
    
    # Display failed predictions
    if failed:
        print(f"\n✗ FAILED PREDICTIONS ({len(failed)}/{len(results)})")
        print("-" * 80)
        for result in failed:
            print(f"  {result['ticker']}: {result['message']}")
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    total_up = sum(1 for r in successful if r['prediction'] == 1)
    total_down = sum(1 for r in successful if r['prediction'] == 0)
    
    if successful:
        avg_confidence = sum(r['confidence'] for r in successful) / len(successful)
        print(f"Total Predictions:     {len(results)}")
        print(f"Successful:            {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
        print(f"Failed:                {len(failed)}")
        print(f"Average Confidence:    {avg_confidence:.2%}")
        print(f"Predicted UP ↑:        {total_up}")
        print(f"Predicted DOWN ↓:      {total_down}")
    else:
        print(f"Total Predictions:     {len(results)}")
        print(f"Failed:                {len(failed)}")
    
    print("=" * 80 + "\n")


def main():
    """Main function for command-line interface"""
    parser = argparse.ArgumentParser(
        description='LSTM Stock Price Predictor - Predict stock movements for tickers'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Predict for all tickers in database'
    )
    
    parser.add_argument(
        '--tickers',
        nargs='+',
        help='Specific tickers to predict (space-separated)'
    )
    
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save predictions to database'
    )
    
    parser.add_argument(
        '--export',
        type=str,
        help='Export results to JSON file'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Display detailed information'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='./lstmModel/fypLSTM.h5',
        help='Path to LSTM model file (default: ./lstmModel/fypLSTM.h5)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.all and not args.tickers:
        parser.print_help()
        logger.error("Please specify either --all or --tickers")
        sys.exit(1)
    
    # Check if model exists
    if not Path(args.model).exists():
        logger.error(f"Model file not found: {args.model}")
        sys.exit(1)
    
    try:
        # Initialize predictor
        predictor = LSTMStockPredictor(args.model)
        
        # Get tickers to predict
        if args.all:
            db_manager = DatabaseManager()
            tickers = db_manager.get_all_tickers()
            db_manager_obj = db_manager
        else:
            tickers = args.tickers
            db_manager_obj = None
        
        if not tickers:
            logger.warning("No tickers to predict")
            sys.exit(0)
        
        # Make predictions
        logger.info(f"Making predictions for {len(tickers)} ticker(s)...")
        results = predictor.predict_batch(tickers)
        
        # Save to database if requested
        saved_count = 0
        if args.save and args.all:
            for result in results:
                if result['status'] == 'success':
                    if db_manager_obj.save_prediction(
                        result['ticker'],
                        result['prediction'],
                        result['prediction_date']
                    ):
                        saved_count += 1
        elif args.save and not args.all:
            logger.warning("--save only works with --all flag (to prevent accidental saves)")
        
        # Display results
        display_results(results, verbose=args.verbose)
        
        # Export results if requested
        if args.export:
            export_results(results, args.export)
        
        # Close database connection if opened
        if db_manager_obj:
            db_manager_obj.close()
        
        # Return success code
        failed = sum(1 for r in results if r['status'] == 'failed')
        sys.exit(0 if failed == 0 else 1)
    
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
