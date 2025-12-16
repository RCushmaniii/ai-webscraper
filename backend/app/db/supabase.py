import logging
from supabase import create_client, Client

from app.core.config import settings

logger = logging.getLogger(__name__)

class SupabaseClient:
    """
    Singleton class for Supabase client.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the Supabase client."""
        try:
            self.url = settings.SUPABASE_URL
            self.key = settings.SUPABASE_KEY
            self.client = create_client(self.url, self.key)
            self.auth_url = f"{self.url}/auth/v1"
            self.supabase_key = self.key
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    def table(self, table_name: str):
        """
        Get a reference to a Supabase table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Supabase table reference
        """
        return self.client.table(table_name)
    
    def auth(self):
        """
        Get the Supabase auth client.
        
        Returns:
            Supabase auth client
        """
        return self.client.auth
    
    def storage(self):
        """
        Get the Supabase storage client.
        
        Returns:
            Supabase storage client
        """
        return self.client.storage
    
    def rpc(self, fn_name, params=None):
        """
        Call a Postgres function via RPC.
        
        Args:
            fn_name: Name of the function
            params: Parameters for the function
            
        Returns:
            Result of the RPC call
        """
        return self.client.rpc(fn_name, params)

# Create a singleton instance
supabase_client = SupabaseClient()
