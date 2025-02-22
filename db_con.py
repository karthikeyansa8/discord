import json
import os
import psycopg2
import traceback

import pandas as pd 
from sqlalchemy import create_engine
from dotenv import load_dotenv
load_dotenv()


host=os.getenv('host')
dbname=os.getenv('dbname')
user=os.getenv('db_username')
password=os.getenv('password')
port=os.getenv('port')


engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}")

def processquery(query: str) -> pd.DataFrame:
    # conn = psycopg2.connect(
    # database=db , user=username, password= password, host=host , port= port
    # )

    """returns the query as pandas dataframe from database
    Args:
    --------
        query (str): query
    
    Returns:
    ---------
        data: pandas dataframe from query
    """
    table = pd.read_sql(query, con=engine)
    # conn.close()
    return table

def create_connection():
    conn = psycopg2.connect(
    database=dbname , user=user, password= password, host=host , port= port,application_name= 'ReprotDjangoData'
    )

    return conn

conn = create_connection()

def excute_query(query:str,vars={}):

    global conn

    try:
        if conn.closed != 0:
            conn = create_connection()
        cursor = conn.cursor()   
        cursor.execute(query=query,vars=vars)
        conn.commit()
    except Exception as e:
        conn.close()
        raise Exception(e)

def excute_query_without_commit(cursor,query):
    try:
        cursor.execute(query=query)
    except Exception as e:
        raise Exception(e)
    

def excute_query_and_return_result(query:str,vars={}):
    try:
        global conn
   
        if conn.closed != 0:
            conn = create_connection()

        cursor = conn.cursor()   
        cursor.execute(query=query,vars=vars)
        data =  cursor.fetchall()

        return data
    except Exception as e:
        print(e)
        print(traceback.print_exc())
        conn.close()
        raise Exception(e)
    

def excute_query_and_return_result_with_cursor(query:str,cursor,arguments=[]):
    try:
        cursor.execute(query=query,vars=arguments)
        data =  cursor.fetchall()
        return data
    except Exception as e:
        print(e)
        print(traceback.print_exc())
        raise Exception(e)

def check_student_present(roll_number):
    ly_learner_id = 0
    query = f"""select count(*),ly_learner_id from school_data.student_detail where roll_number = '{roll_number}' group by roll_number"""
    data = excute_query_and_return_result(query=query)
    roll_number_count,ly_learner_id = data[0]
    
    if roll_number_count == 1:
        return True,ly_learner_id
    else:
        return False,ly_learner_id

def get_student_password_by_username_nad_name_from_db(username):
    username = str(username).lower()
    
    query = f"""with student_data as (select roll_number,student_name,ly_password, concat(school_acronym,'-',class,section) as std,school_acronym
    from school_data.student_detail sd
    join school_data.school_section_detail ssd on sd.section_id = ssd.section_id
    join school_data.school_detail ssdd on ssdd.school_id = ssd.school_id
    where LOWER(roll_number) like '%%{username}%%' OR LOWER(student_name) like '%%{username}%%'
    limit 5)

    select concat('Name:',student_name,'\n','School:',school_acronym,'\n','Class:',std,'\n','UserName:',roll_number) as final_string,ly_password
    from student_data"""
    
    list_of_data_df = processquery(query=query)
    
    # list_of_data_df = list_of_data_df.set_index('final_string')
    
    list_of_data_df = json.loads(list_of_data_df.to_json(orient='records'))
    
    print(list_of_data_df)
    
    return list_of_data_df

def get_student_password_by_school_name_class_section(school_name,class_name,section_name):
    
   
    query = f"""select
	roll_number,
            student_name,ly_password
        from
            school_data.student_detail sd
            join school_data.school_section_detail ssd on sd.section_id = ssd.section_id
            join school_data.school_detail sch_detail on sch_detail.school_id = ssd.school_id
            where ( school_acronym ilike '{school_name}%%' or school_name like '{school_name}%%' )and section ilike '{section_name}%%' and class = '{class_name}'
        order by sch_detail.school_id,class,section,substring(roll_number,2)::int
        """
    
    list_of_data_df = processquery(query=query)

    return list_of_data_df

def get_student_questions_in_worksheet(roll_number:str,school_chapter_id):
    roll_number = roll_number.upper()

    if school_chapter_id == None:
        return
    
    try:
        query_for_questions = f"""select question_track from content.worksheet_track 
        where school_chapter_id = {school_chapter_id} and roll_number = '{roll_number}'"""

        result = excute_query_and_return_result(query=query_for_questions)[0][0]

        return str(result)
    except Exception as e:
        return "No data found"

if __name__ == "__main__":

    student_list = get_student_questions_in_worksheet(roll_number="D127135",school_chapter_id="2120")    
    print(student_list) 