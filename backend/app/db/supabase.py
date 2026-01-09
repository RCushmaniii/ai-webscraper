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

            if not self.url or not self.key:
                raise ValueError(
                    "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_SECRET_KEY (or SUPABASE_KEY) in backend/.env."
                )

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

    def get_client_with_auth(self, token: str):
        """
        Create a Supabase client with user's auth token.
        This ensures RLS policies work correctly.

        Args:
            token: User's JWT token

        Returns:
            Supabase client with auth token set
        """
        # Create a new client instance with the user's token
        client = create_client(self.url, self.key)
        # Set the auth header for RLS
        client.postgrest.auth(token)
        return client
    
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
