"""
MongoDB Setup Script for AI Dungeon Master

This script helps set up a MongoDB connection string for testing.
It can either:
1. Create a .env file with a MongoDB connection string
2. Test the connection to verify it works

Usage:
python setup_mongodb.py --create
python setup_mongodb.py --test
"""

import os
import sys
import argparse
import getpass
from dotenv import load_dotenv

def create_mongodb_connection():
    """Create a MongoDB connection string and save it to .env file"""
    print("===== MongoDB Connection Setup =====")
    print("This script will help you set up a MongoDB connection for your AI Dungeon Master app.")
    print("You can use MongoDB Atlas (cloud) or a local MongoDB instance.")
    print()
    
    connection_type = input("Do you want to use MongoDB Atlas (A) or local MongoDB (L)? [A/L]: ").strip().upper()
    
    if connection_type == 'A':
        # MongoDB Atlas setup
        print("\n--- MongoDB Atlas Setup ---")
        print("You'll need your Atlas connection credentials.")
        
        username = input("Atlas Username: ").strip()
        password = getpass.getpass("Atlas Password: ")
        cluster_url = input("Cluster URL (e.g., cluster0.abc123.mongodb.net): ").strip()
        db_name = input("Database Name [ai_dungeon_master]: ").strip() or "ai_dungeon_master"
        
        # Build the connection string
        mongo_uri = f"mongodb+srv://{username}:{password}@{cluster_url}/{db_name}?retryWrites=true&w=majority"
        
    elif connection_type == 'L':
        # Local MongoDB setup
        print("\n--- Local MongoDB Setup ---")
        
        host = input("MongoDB Host [localhost]: ").strip() or "localhost"
        port = input("MongoDB Port [27017]: ").strip() or "27017"
        db_name = input("Database Name [ai_dungeon_master]: ").strip() or "ai_dungeon_master"
        
        use_auth = input("Does your local MongoDB require authentication? [y/N]: ").strip().lower() == 'y'
        
        if use_auth:
            username = input("MongoDB Username: ").strip()
            password = getpass.getpass("MongoDB Password: ")
            mongo_uri = f"mongodb://{username}:{password}@{host}:{port}/{db_name}"
        else:
            mongo_uri = f"mongodb://{host}:{port}/{db_name}"
    
    else:
        print("Invalid choice. Please run the script again and select either A or L.")
        return
    
    # Create or update .env file
    try:
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                env_content = f.read()
            
            # Check if MONGO_URI already exists
            if 'MONGO_URI=' in env_content:
                # Replace existing MONGO_URI
                lines = env_content.split('\n')
                new_lines = []
                for line in lines:
                    if line.startswith('MONGO_URI='):
                        new_lines.append(f'MONGO_URI="{mongo_uri}"')
                    else:
                        new_lines.append(line)
                
                env_content = '\n'.join(new_lines)
            else:
                # Add MONGO_URI to existing file
                env_content += f'\nMONGO_URI="{mongo_uri}"'
            
            with open('.env', 'w') as f:
                f.write(env_content)
        else:
            # Create new .env file
            with open('.env', 'w') as f:
                f.write(f'MONGO_URI="{mongo_uri}"\n')
        
        print("\n✅ MongoDB connection string saved to .env file.")
        print("You can now run your application with database functionality.")
        
    except Exception as e:
        print(f"\n❌ Error saving connection string: {e}")

def test_mongodb_connection():
    """Test the MongoDB connection from .env file"""
    print("===== Testing MongoDB Connection =====")
    
    # Load environment variables
    load_dotenv()
    
    # Check if MONGO_URI exists
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("❌ MONGO_URI not found in .env file.")
        print("Run this script with --create to set up the connection string.")
        return
    
    # Try to connect to MongoDB
    try:
        from pymongo import MongoClient
        
        # Hide password in output
        display_uri = mongo_uri.replace('mongodb+srv://', 'mongodb+srv://****:****@')
        if '://' in display_uri and '@' in display_uri:
            parts = display_uri.split('@')
            protocol_parts = parts[0].split('://')
            display_uri = f"{protocol_parts[0]}://****:****@{parts[1]}"
        
        print(f"Connecting to: {display_uri}")
        
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        
        db = client.get_database()
        collections = db.list_collection_names()
        
        print("✅ Successfully connected to MongoDB!")
        print(f"Database name: {db.name}")
        print(f"Collections: {', '.join(collections) if collections else 'No collections yet'}")
        
        # Create any missing collections
        required_collections = ['users', 'characters', 'character_drafts', 'campaigns', 'sessions']
        for collection in required_collections:
            if collection not in collections:
                db.create_collection(collection)
                print(f"Created missing collection: {collection}")
                
                # Add indexes for users collection
                if collection == 'users':
                    db.users.create_index("username", unique=True)
                    print("Added unique index on username")
        
        print("\nYour MongoDB connection is working correctly!")
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("\nPlease check your connection string and make sure your MongoDB instance is running.")
        print("If using MongoDB Atlas, check your network connection and whitelist your IP address.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MongoDB Setup for AI Dungeon Master")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--create', action='store_true', help='Create MongoDB connection string')
    group.add_argument('--test', action='store_true', help='Test MongoDB connection')
    
    args = parser.parse_args()
    
    if args.create:
        create_mongodb_connection()
    elif args.test:
        test_mongodb_connection()