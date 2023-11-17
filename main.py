from fastapi import FastAPI
from typing import Union
from pydantic import BaseModel
from openai import OpenAI
import json
import gspread
import os



client = OpenAI(api_key='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')
sa = gspread.service_account(filename='service_account.json')

sh = sa.open("Car Dealer")
wks = sh.worksheet("Sheet1")

print(f'row count{wks.row_count}')
print(wks.get_all_values())
wks.update('A2', [[1, 2,3, 4]])
print(wks.col_count)

insert_row  = [1,2,4,5,6]
wks.append_row(insert_row,table_range="A1")


class OpenAiReq(BaseModel):
    context: str
    columns: str
    data: str

app = FastAPI()

@app.post("/openai")
async def openai(req: OpenAiReq):

    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", 
         "content": """You are a text parser which takes unstructred data and return
           structured data in the form of json object,Given a context ,column names
               and unstructured data for a  csv file,  return json object for the data as ,
               \n{\n column1: relevant data,\ncolumn2: relevant data,\n......\n}\nif data is not present use NA,
                 return only the json object.\n\n Example for  a car dealership the columns are brand ,
                   make, manufacturing year,  ownership number, price, km run.
                   \n\nunstructured data: '2017 Sigma 4 auto 4by4 delhi 1st 1.29lac km done, 21.5 lac '.\n```\n
                   structured output: {\nmanufacturing year: 2017,\nkm_run: 129000,\nprice: 2150000,\nownership_no:NA,\nmake: NA,\nbrand:NA\n}\n```\n\n
                   """f"""
                   given context:{req.context},
                   given columns:{req.columns}, 
                   given unstructured data: '{req.data}'.\ngive json output."""
         },
       
    ]
)
    open_res= completion.choices[0].message.content
    input_row = parse_and_clean(open_res).values()
    wks.append_row(list(input_row),table_range="A1")
    return parse_and_clean(completion.choices[0].message.content)



def parse_and_clean(json_string):
    # Convert the JSON string to a Python dictionary
    data_dict = json.loads(json_string)

    # Remove '\n' from dictionary keys and values
    cleaned_dict = {key.replace('\n', ''): value.replace('\n', '') if isinstance(value, str) else value for key, value in data_dict.items()}

    return cleaned_dict


# @app.post("/context/{context}")
# async def setContext(){

# }