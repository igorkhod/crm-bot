from dotenv import load_dotenv
load_dotenv('token.env')
TOKEN = os.getenv('TOKEN')
API_KEY = os.getenv('IGOR_KHOD_API_KEY') - "DEEPSEEK_API"
