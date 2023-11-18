from fastapi import FastAPI
from typing import Union
from pydantic import BaseModel
from openai import OpenAI
import json
import gspread


from fastapi.middleware.cors import CORSMiddleware
import os
import dotenv

dotenv.load_dotenv()

app = FastAPI()

origins = [
    "http://localhost:5173",  # React app
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




api_key = os.environ.get('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)
sa = gspread.service_account(filename='service_account.json')


class OpenAiReq(BaseModel):
    context: str
    columns: str
    data: str


@app.post("/openai")
async def openai(req: OpenAiReq):

#     return  {
#     "context":"a car dealership",
#     "columns":"brand, km_run, price,model, year_of_make",
#     "data":"audi a6 2019 23000km 2lac"
# }

    print("firls")
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo-1106",
    messages=[
        {
        "role": "system", 
         "content": """You are a text parser which takes unstructred data and return
                    structured data in the form of json object,Given a context ,column names
                    and unstructured data for a  csv file,  return json object for the data as ,
                    \n{\n "column1": "relevant data",\n"column2": "relevant data"   ,\n......\n}\nif data is not present use NA,
                    return only the json object.\n\n Example for  a car dealership the columns are brand ,
                    make, manufacturing year,  ownership number, price, km run.
                    \n\nunstructured data: '2017 Sigma 4 auto 4by4 delhi 1st 1.29lac km done, 21.5 lac '.\n```\n
                    structured output: {\nmanufacturing year: 2017,\nkm_run: 129000,\nprice: 2150000,\nownership_no:NA,\nmake: NA,\nbrand:NA\n}\n```\n\n
                    """f"""
                    given context:{req.context},
                    given columns:{req.columns}, 
                    given unstructured data: '{req.data}'.\ngive json output, make sure to keep the quotes properly.
                    Also column order should be same as order of 'given columns', take care to make sure that similar columns and datas are not mixed up.
                    convert numbers like 2k to 2000 and 2lac or 2lakh to 200000, dates should be converted to day-month-year, use context to check whether conversion is needed example in case of milage column and value 12mi , mi means mileage and not million so return just 12.
\n\nAdditionally, consider the following cases for better data parsing:\n
- Identify and handle cases where abbreviations are used in unstructured data. For example, 'mi' could represent mileage, and 'mn' could represent million.
- Recognize variations of numeric representations, such as '12k' for 12000 and '1.5m' for 1500000.
- Handle cases where multiple units are used for the same quantity, such as '2kgs' for 2 kilograms or '3lbs' for 3 pounds.
- Account for variations in date formats and convert them to a consistent format (day-month-year).
- Identify and handle special cases mentioned in the context, such as 'lakh' or 'lac' for the Indian numbering system (1 lakh = 100,000).
- Ensure that the parser is robust to handle missing or incomplete data, assigning 'NA' where appropriate.
- Consider implementing checks for common abbreviations and acronyms relevant to the given context and columns.
- remove unit names and return only hard numbers for columns that take number values
- context based for mileage column 25mi mileage means return just 25
    
- always return json string dont return json code
                    """
         },
       
        ]
    )
    open_res= completion.choices[0].message.content
    print(open_res)

    return parse_and_clean(completion.choices[0].message.content)

@app.post("/addrow/{sheet_name}")
async def addrow(sheet_name:str, value: dict):
    print("add row")
    print(f"sheet_name,{sheet_name.strip()}")
    sh = sa.open(sheet_name.strip())
    wks = sh.worksheet("Sheet1")    
    wks.append_row(list(value.values()),table_range="A1")
    print(value.values())
    return value




def parse_and_clean(json_string):
    data_dict = json.loads(json_string)
    cleaned_dict = {key.replace('\n', ''): value.replace('\n', '') if isinstance(value, str) else value for key, value in data_dict.items()}
    return cleaned_dict

