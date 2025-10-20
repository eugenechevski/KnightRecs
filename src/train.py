"""
KnightRecs Model Training Script

Train a collaborative filtering SVD model on MovieLens ratings.
Uses scikit-surprise library: Reader, Dataset, SVD(n_factors=50)
Split 80/20, evaluate RMSE, save with pickle.
"""

import pandas as pd
import pickle
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split
from surprise import accuracy
import os


def load_data():
    """Load MovieLens ratings data."""
    print("Loading MovieLens dataset...")
    ratings_path = os.path.join("ml-latest", "ratings.csv")
    
    # Load ratings data
    ratings_df = pd.read_csv(ratings_path)
    
    print(f"Loaded {len(ratings_df):,} ratings")
    print(f"Number of users: {ratings_df['userId'].nunique():,}")
    print(f"Number of movies: {ratings_df['movieId'].nunique():,}")
    
    return ratings_df


def sample_data(ratings_df, sample_size=1_000_000):
    """
    Sample data for faster training during development.
    For production, remove this or use full dataset.
    """
    if len(ratings_df) > sample_size:
        print(f"\nSampling {sample_size:,} ratings for faster training...")
        # Sample users first to maintain user history
        unique_users = ratings_df['userId'].unique()
        sampled_users = pd.Series(unique_users).sample(n=int(sample_size / 100), random_state=42)
        ratings_df = ratings_df[ratings_df['userId'].isin(sampled_users)]
        
        # If still too large, sample randomly
        if len(ratings_df) > sample_size:
            ratings_df = ratings_df.sample(n=sample_size, random_state=42)
        
        print(f"Sampled to {len(ratings_df):,} ratings")
        print(f"Sampled users: {ratings_df['userId'].nunique():,}")
        print(f"Sampled movies: {ratings_df['movieId'].nunique():,}")
    
    return ratings_df


def train_model(ratings_df):
    """
    Train a collaborative filtering SVD model.
    Uses surprise library with SVD algorithm.
    """
    print("\nPreparing data for Surprise library...")
    
    # Prepare data for Surprise (rating scale 0.5 to 5.0)
    reader = Reader(rating_scale=(0.5, 5.0))
    data = Dataset.load_from_df(ratings_df[['userId', 'movieId', 'rating']], reader)
    
    # Split data for training and validation (80/20)
    print("Splitting data (80% train, 20% test)...")
    trainset, testset = train_test_split(data, test_size=0.2, random_state=42)
    
    # Define the SVD model and train it
    print("\nTraining SVD model (n_factors=50)...")
    print("This may take a few minutes...")
    model = SVD(n_factors=50, n_epochs=20, random_state=42, verbose=True)
    model.fit(trainset)
    
    # Evaluate on test set
    print("\nEvaluating model on test set...")
    predictions = model.test(testset)
    rmse = accuracy.rmse(predictions, verbose=True)
    mae = accuracy.mae(predictions, verbose=True)
    
    print(f"\nModel Performance:")
    print(f"  RMSE: {rmse:.4f}")
    print(f"  MAE:  {mae:.4f}")
    
    return model, trainset


def save_model(model, trainset):
    """Save the trained model to disk."""
    print("\nSaving trained model...")
    
    # Save model
    with open("model.pkl", "wb") as f:
        pickle.dump(model, f)
    
    # Save trainset (needed for getting user's rated items)
    with open("trainset.pkl", "wb") as f:
        pickle.dump(trainset, f)
    
    print("Model saved to model.pkl")
    print("Trainset saved to trainset.pkl")


def main():
    """Main training pipeline."""
    print("=" * 60)
    print("KnightRecs - Movie Recommendation Model Training")
    print("=" * 60)
    
    # Load data
    ratings_df = load_data()
    
    # Sample data for faster training (optional)
    # Comment out the next line to use full dataset
    ratings_df = sample_data(ratings_df, sample_size=1_000_000)
    
    # Train model
    model, trainset = train_model(ratings_df)
    
    # Save model
    save_model(model, trainset)
    
    print("\n" + "=" * 60)
    print("Training complete! Model ready for deployment.")
    print("=" * 60)


if __name__ == "__main__":
    main()
