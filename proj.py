from pymongo import MongoClient, collection
from os import getenv
from dotenv import load_dotenv, find_dotenv
import matplotlib.pyplot as plt
import numpy as np
import math
import pandas as pd
from prettytable import PrettyTable

def get_database():

    #Connect python to mongodb atlas using the connection string
    load_dotenv(find_dotenv())
    client = MongoClient(getenv("CONNECTION_STRING"))
    _client_db = client["StackOverflow2022"]
    
    return _client_db

def analyze_tech_stack_preference(data: collection.Collection, data_count: int):

    #To analyze which tech stack is associated with higher salaries and the age group. 
    result = data.aggregate(
        [
            {
                "$match": {
                    "$and": [
                        {
                            "LanguageHaveWorkedWith": { "$exists": True, "$ne": "NA" },
                        },
                        {
                            "Country": {"$in": ["United States of America", "India", "Canada", "Australia", "United Kingdom of Great Britain and Northern Ireland"]},
                        },
                        {
                            "WebframeHaveWorkedWith": { "$exists": True, "$ne": "NA" },
                        },
                        {
                            "CompTotal": { "$exists": True, "$ne": "NA" }
                        },
                        {
                            "CompFreq": "Yearly"
                        }
                    ]
                }
            },
            {
                "$addFields": {
                    "LanguageList": {"$split": ["$LanguageHaveWorkedWith", ";"]},
                    "WebframeList": {"$split": ["$WebframeHaveWorkedWith", ";"]}
                }
            },
            {
                "$unwind": "$LanguageList"
            },
            {
                "$unwind": "$WebframeList"
            },
            {
                "$group": {
                    "_id": {
                        "Country": "$Country",
                        "TechnologyStack": {"$concat": ["$LanguageList", ";", "$WebframeList"]},
                        "CompFreq": "$CompFreq",
                        "OrgSize": {
                            "$switch": {
                                "branches": [
                                    { "case": { "$lte": ["$OrgSize", 10] }, "then": "Small" },
                                    { "case": { "$lte": ["$OrgSize", 100] }, "then": "Medium" },
                                    { "case": { "$lte": ["$OrgSize", 1000] }, "then": "Large" },
                                    { "case": { "$gte": ["$OrgSize", 10000] }, "then": "Very Large" }
                                ],
                                "default": "Unknown"
                            }
                        }
                    },
                    "Count": {"$sum": 1},
                    "CompTotal": { "$avg": "$CompTotal" }
                }
            },
            {
                "$group": {
                    "_id": {
                        "Country": "$_id.Country",
                        "OrgSize": "$_id.OrgSize"
                    },
                    "TechnologyStacks": {
                        "$push": {
                            "TechnologyStack": "$_id.TechnologyStack",
                            "Count": "$Count",
                            "CompTotal": "$CompTotal",
                            "CompFreq": "$_id.CompFreq"
                        }                        
                    },
                    "TotalDevelopers": {"$sum": "$Count"}
                }
            },
            {
                "$addFields": {
                    "DominantStack": {
                        "$reduce": {
                            "input": "$TechnologyStacks",
                            "initialValue": {"TechnologyStack": "", "Count": 0},
                            "in": {
                                "$cond": {
                                    "if": {"$gt": ["$$this.Count", "$$value.Count"]},
                                    "then": "$$this",
                                    "else": "$$value"
                                }
                            }
                        }
                    }
                }
            },
            {
                "$sort": {"TotalDevelopers": -1}
            },
            {
                "$project": {
                    "Country": "$_id.Country",
                    "OrgSize": "$_id.OrgSize",
                    "DominantStack": 1,
                    "LeastDominantStack": {"$arrayElemAt": ["$TechnologyStacks", -1]},
                    "TotalDevelopers": 1,
                    "_id": 0
                }
            },
            {
                "$limit": 5
            }
        ]
    )
    
    return result

def analyze_mental_health_impact(data: collection.Collection, data_count: int):

    result = data.aggregate(
        [        
            {
                "$match": {
                    "$and": [
                        { "MentalHealth": { "$exists": True, "$ne": "NA" } },
                        { "Gender": 
                            {"$regex": "^(?!.*(?:Or, in your own words:|Prefer not to say)).*$", "$ne": "NA"}
                        },
                        { "Ethnicity": 
                            {"$regex": "^(?!.*(?:Or, in your own words:|Prefer not to say)).*$", "$ne": "NA"}
                        }
                    ]
                }
            },
            {
                "$addFields": {
                    "Gender": {
                        "$split": ["$Gender", ";"]
                    }
                }
            },
            {
                "$unwind": "$Gender"
            },
            {
                "$addFields": {
                    "Ethnicity": {
                        "$split": ["$Ethnicity", ";"]
                    }
                }
            },
            {
                "$unwind": "$Ethnicity"
            },
            {
                "$addFields": {
                    "CodingActivities": {
                        "$split": ["$CodingActivities", ";"]
                    },
                    "PurchaseInfluence": {
                        "$split": ["$PurchaseInfluence", ";"]
                    }
                }
            },
            {
                "$addFields": {
                    "coding_activities_count": {
                        "$size": "$CodingActivities"
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "Gender": "$Gender",
                        "Ethnicity": "$Ethnicity",
                    },                        
                    "total_respondents": { "$sum": 1 },
                    "coding_activities_count": { "$max": "$coding_activities_count" },
                    "total_mental_health_issues": {
                        "$sum": {
                            "$cond": [
                                { 
                                    "$and": [
                                { "$ne": [ "$MentalHealth", "None of the above" ] },
                                { "$gt": [ "$coding_activities_count", 2 ] },
                                { "$in": [ "I have a great deal of influence", "$PurchaseInfluence" ] }
                                ]
                                },
                                1,
                                0
                            ]
                        }
                    },
                    "likely_mental_health_issues": {
                        "$sum": {
                        "$cond": [
                            {
                            "$and": [
                                { "$eq": [ "$MentalHealth", "None of the above" ] },
                                { "$gt": [ "$coding_activities_count", 2 ] },
                                { "$in": [ "I have a great deal of influence", "$PurchaseInfluence" ] }
                            ]
                            },
                            1,
                            0
                        ]
                        }
                    }
                }
            },
            {
                "$addFields": {
                "percentage_mental_health_issues": {
                    "$multiply": [
                    { "$divide": [ "$total_mental_health_issues", "$total_respondents" ] },
                    100
                    ]
                },
                "percentage_likely_mental_health_issues": {
                    "$multiply": [
                    { "$divide": [ "$likely_mental_health_issues", "$total_respondents" ] },
                    100
                    ]
                }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "Gender": "$_id.Gender",
                    "Ethnicity": "$_id.Ethnicity",
                    "total_respondents": 1,                
                    "percentage_mental_health_issues": 1,
                    "percentage_likely_mental_health_issues": 1,
                    "coding_activities_count": 1
                }
            },
            {
                "$sort": { "percentage_likely_mental_health_issues": -1 }
            },
            {
                "$limit": 5
            }
        ]
    )
    return result

def analyze_remote_work_impact(data: collection.Collection, data_count: int):

    result = data.aggregate(
        [        
            {
                "$match": {
                    "$and": [
                        {
                            "MainBranch": { "$exists": True, "$eq": "I am a developer by profession" }
                        },
                        {
                            "Employment": "Employed, full-time",
                        },
                        {
                            "$or": [
                                { "RemoteWork": { "$exists": True, "$eq": "Fully remote" } },
                                { "RemoteWork": { "$exists": True, "$eq": "Hybrid (some remote, some in-person)" } }
                            ]
                        },
                        {
                            "YearsCodePro": { "$exists": True, "$ne": "NA" },
                        },
                        {
                            "ConvertedCompYearly": { "$exists": True, "$ne": "NA" },
                        }
                    ],
                }
            },
            {
                "$addFields": {
                    "AgeDigits": {
                        "$regexFind": {
                            "input": "$Age",
                            "regex": "\\d+"
                        }
                    }
                }
            },
            {
                "$addFields": {
                    "AgeInt": {
                        "$toInt": "$AgeDigits.match"
                    }
                }
            },
            {
                "$addFields": {
                    "AgeGroup": {
                        "$switch": {
                            "branches": [
                                { "case": { "$lte": [ "$AgeInt", 24 ] }, "then": "Under 25" },
                                { "case": { "$lte": [ "$AgeInt", 34 ] }, "then": "25-35" },
                                { "case": { "$lte": [ "$AgeInt", 44 ] }, "then": "35-45" },
                                { "case": { "$lte": [ "$AgeInt", 54 ] }, "then": "45-55" },
                                { "case": { "$gte": [ "$AgeInt", 55 ] }, "then": "55+" }
                            ]
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "Age": "$AgeGroup",
                        "RemoteWork": "$RemoteWork"
                    },
                    "AvgCompensation": { "$avg": "$ConvertedCompYearly"},
                    "AvgYearsExp": { "$avg": "$YearsCodePro"},
                    "Count": { "$sum": 1}
                }
            },
            {
                "$project":{
                    "_id": 0,
                    "Age": "$_id.Age",
                    "RemoteWork": "$_id.RemoteWork",
                    "AvgCompensation": 1,
                    "AvgYearsExp": 1,
                    "Count": 1
                }
            },
            {"$sort": {"Age": 1, "RemoteWork": 1}},
        ]
    )
    return result

def employed_vs_unemployed_gap(data: collection.Collection, data_count: int):

    result = data.aggregate(
        [
            {
                "$facet": {
                    "employedDevelopers": [
                        {
                        "$match": {
                            "$and": [
                            {
                                "MainBranch": {
                                "$exists": True,
                                "$in": [
                                    "I am a developer by profession",
                                    "I used to be a developer by profession, but no longer am"
                                ]
                                }
                            },
                            {
                                "LearnCode": {
                                "$regex": "^(?!.*(?:Coding Bootcamp|School|Online Courses or Certification)).*$",
                                "$ne": "NA"
                                }
                            },
                            {
                                "$or": [
                                {
                                    "Employment": "Employed, full-time"
                                },
                                {
                                    "Employment": "Employed, full-time",
                                    "OrgSize": "Just me - I am a freelancer, sole proprietor, etc."
                                }
                                ]
                            },
                            {
                                "LanguageHaveWorkedWith" : { "$exists": True, "$ne": "NA" }
                            }
                            ]
                        }
                        },
                        {
                            "$addFields": {
                                "Languages": {
                                    "$split": ["$LanguageHaveWorkedWith", ";"]
                                }
                            }
                        },
                        {
                            "$unwind": "$Languages"
                        },
                        {
                        "$group": {
                            "_id": {
                            "Employment": "$Employment",
                            "OrgSize": "$OrgSize",
                            "EdLevel": "$EdLevel",
                            "Country": "$Country"
                            },
                            "Count": {
                            "$sum": 1
                            },
                            "LanguageHaveWorkedWith": {
                                "$addToSet": "$Languages"
                            }
                        }
                        },
                        {
                        "$project": {
                            "Employment": "$_id.Employment",
                            "OrgSize": "$_id.OrgSize",
                            "EdLevel": "$_id.EdLevel",
                            "Country": "$_id.Country",
                            "Count": "$Count",
                            "LanguageHaveWorkedWith": 1,
                            "_id": 0
                        }
                        },
                        {
                        "$sort": {
                            "Count": -1
                        }
                        },
                        {
                        "$limit": 5
                        }
                    ],
                    "unemployedDevelopers": [
                    {
                    "$match": {
                        "$and": [
                        {
                            "MainBranch": {
                            "$exists": True,
                            "$in": [
                                "I am a developer by profession",
                                "I used to be a developer by profession, but no longer am"
                            ]
                            }
                        },
                        {
                            "LearnCode": {
                            "$regex": "^(?!.*(?:Coding Bootcamp|School|Online Courses or Certification)).*$",
                            "$ne": "NA"
                            }
                        },
                        {
                            "Employment": "Not employed, but looking for work"
                        },
                        {
                            "LanguageHaveWorkedWith": { "$exists": True, "$ne": "NA"}
                        }
                        ]
                    }
                    },
                    {
                        "$addFields": {
                            "Languages": {
                                "$split": ["$LanguageHaveWorkedWith", ";"]
                            }
                        }
                    },
                    {
                        "$unwind": "$Languages"
                    },
                    {
                    "$group": {
                        "_id": {
                        "EdLevel": "$EdLevel",
                        "Country": "$Country"
                        },
                        "Count": {
                        "$sum": 1
                        },
                        "LanguageHaveWorkedWith": {
                            "$addToSet": "$Languages"
                        }
                    }
                    },
                    {
                    "$project": {
                        "EdLevel": "$_id.EdLevel",
                        "Country": "$_id.Country",
                        "Count": "$Count",
                        "LanguageHaveWorkedWith": 1,
                        "_id": 0
                    }
                    },
                    {
                    "$sort": {
                        "Count": -1
                    }
                    },
                    {
                        "$limit": 5
                    }
                ]
                }
            },
            # {
            #     "$project": {
            #         "eL": "$employedDevelopers",
            #         "uL": "$unemployedDevelopers",
            #         "unemployedSkillsLack": {
            #             "$setDifference": [
            #                 "$employedDevelopers.LanguageHaveWorkedWith",
            #                 "$unemployedDevelopers.LanguageHaveWorkedWith"
            #             ]
            #         }
            #     }
            # }
        ]
    )
    return result

def job_title_and_common_lang_used(data: collection.Collection, data_count: int):
    result = data.aggregate([
        { 
            "$match": { 
                "DevType": { "$exists": True, "$ne": "NA" }, 
                "LanguageHaveWorkedWith": { "$exists": True, "$ne": "NA" },
                "YearsCodePro": { "$exists": True, "$ne": "NA" }, 
                "ConvertedCompYearly": { "$exists": True, "$ne": "NA" },
                "Employment": "Employed, full-time"
            } 
        },
        { "$addFields": { 
            "DevTypeArray": { "$split": ["$DevType", ";"] }, 
            "LanguageArray": { "$split": ["$LanguageHaveWorkedWith", ";"] }            
            }
        },
        { "$unwind": "$DevTypeArray" },
        { "$unwind": "$LanguageArray" },
        { "$group": { 
            "_id": { "DevType": "$DevTypeArray", "Language": "$LanguageArray" }, 
            "count": { "$sum": 1 }, 
            "YearsOfExp": { "$avg": "$YearsCodePro" }, 
            "Compensation": { "$avg": "$ConvertedCompYearly" }
        } 
        },
        { "$sort": { "_id.DevType": 1, "count": -1 } },
        { "$group": { 
            "_id": "$_id.DevType", 
            "languages": { "$push": { "Language": "$_id.Language", "count": "$count" } }, 
            "YearsOfExp": { "$avg": "$YearsOfExp" }, 
            "Compensation": { "$avg": "$Compensation" } 
        } },
        { "$project": { "JobTitle": "$_id", "_id": 0, "TopLanguages": { "$slice": [ "$languages", 5 ] }, "YearsOfExp": 1, "Compensation": 1} }
    ])
    return result

def plot_analyze_result_1(data: collection.Collection, data_count: int):
    
    # Create a list of dictionaries containing the data to plot
    sdata = []
    max_actual, max_likely = float("-inf"), float("-inf")
    min_actual, min_likely = float("inf"), float("inf")
    for doc in data:
        max_actual = max(doc['percentage_likely_mental_health_issues'], doc['percentage_mental_health_issues'], max_actual)
        max_likely = max(doc['percentage_likely_mental_health_issues'], doc['percentage_mental_health_issues'], max_likely)
        min_actual = min(doc['percentage_likely_mental_health_issues'], doc['percentage_mental_health_issues'], min_actual)
        min_likely = min(doc['percentage_likely_mental_health_issues'], doc['percentage_mental_health_issues'], min_likely)
        sdata.append(doc)
    
    # Create a list of genders and their corresponding colors
    genders = ['Man', 'Woman', 'Non-binary']

    # Create two subplots side-by-side
    fig, ax = plt.subplots(1, 2, figsize=(10, 5))

    for i in range(2):
        ax[i].bar([d['Ethnicity'] + " \n" + d['Gender'][:5] for d in sdata], [d['percentage_mental_health_issues'] if i == 0 else d['percentage_likely_mental_health_issues'] for d in sdata])
        ax[i].set_title('Mental Health Issues' if i == 0 else 'Likely Mental Health Issues')
        ax[i].set_xlabel('Ethnicity')
        ax[i].set_ylabel('Percentage')
        ax[i].set_ylim([math.floor(min_actual), math.ceil(max_actual)] if i == 0 else [math.floor(min_likely), math.ceil(max_likely)])
        ax[i].tick_params(axis='x')
        ax[i].legend(genders, loc='upper left')
        
    # Add text on each bar chart of coding_activities_count
    for i, v in enumerate(sdata):
        ax[0].annotate(str(v['total_respondents']), xy=(i, v['percentage_mental_health_issues']), ha='center', va='bottom')
        ax[1].annotate(str(v['coding_activities_count']), xy=(i, v['percentage_likely_mental_health_issues']), ha='center', va='bottom')

    # Set the overall title of the plot
    fig.suptitle('Mental Health Issues by Gender and Ethnicity')

    # Display the plot
    plt.show()

    return

def plot_analyze_result_2(result: collection.Collection, data_count: int):
    data = []
    for i in result:
        data.append(i)

    table = PrettyTable()
    table.field_names = ["Country", "Org Size","Total Dev", "Dominant Technology Stack", "Dominant Count", "Dominant CompTotal", "Least Dominant Technology Stack", "Least Dominant Count", "Least Dominant CompTotal"]

    for item in data:
        table.add_row([item["Country"] if item['Country'] != "United Kingdom of Great Britain and Northern Ireland" else "United Kingdom",
                    item["OrgSize"],
                    item["TotalDevelopers"],
                    item["DominantStack"]["TechnologyStack"],
                    item["DominantStack"]["Count"],
                    item["DominantStack"]["CompTotal"],
                    item["LeastDominantStack"]["TechnologyStack"],
                    item["LeastDominantStack"]["Count"],
                    item["LeastDominantStack"]["CompTotal"]])    
    print(table)
    return table

def plot_analyze_result_3(data: collection.Collection, count: int):
    
    employed_data = {"Employment": [], "OrgSize": [], "EdLevel": [], "Country": [], "LanguageHaveWorkedWith": [], "Count": []}
    unemployed_data = {"EdLevel": [], "Country": [], "LanguageHaveWorkedWith": [], "Count": []}

    for i in data:
        employedDevelopers = i['employedDevelopers']
        unemployedDevelopers = i['unemployedDevelopers']
        
        for developer in employedDevelopers:
            employed_data["Employment"].append(developer["Employment"])
            employed_data["OrgSize"].append(developer["OrgSize"])
            employed_data["EdLevel"].append(developer["EdLevel"])
            employed_data["Country"].append(developer["Country"])
            employed_data["LanguageHaveWorkedWith"].append(', '.join(developer["LanguageHaveWorkedWith"]))
            employed_data["Count"].append(developer["Count"])
        
        for developer in unemployedDevelopers:
            unemployed_data["EdLevel"].append(developer["EdLevel"])
            unemployed_data["Country"].append(developer["Country"])
            unemployed_data["LanguageHaveWorkedWith"].append(', '.join(developer["LanguageHaveWorkedWith"]))
            unemployed_data["Count"].append(developer["Count"])

    employed_table = PrettyTable()
    employed_table.field_names = list(employed_data.keys())

    for row in zip(*employed_data.values()):
        # Truncate LanguageHaveWorkedWith to 5 values with wrap
        lhww = row[4].split(', ')
        if len(lhww) > 5:
            lhww = lhww[:5]
            lhww[4] += '...'
        row = row[:4] + (', '.join(lhww),) + row[5:]
        employed_table.add_row(row)

    unemployed_table = PrettyTable()
    unemployed_table.field_names = list(unemployed_data.keys())

    for row in zip(*unemployed_data.values()):
        # Truncate LanguageHaveWorkedWith to 5 values with wrap
        lhww = row[2].split(', ')
        if len(lhww) > 5:
            lhww = lhww[:5]
            lhww[4] += '...'
        row = row[:2] + (', '.join(lhww),) + row[3:]
        unemployed_table.add_row(row)

    print("Employed Developers:\n")
    print(employed_table)

    print("\nUnemployed Developers:\n")
    print(unemployed_table)
    return

def plot_analyze_result_4(data: collection.Collection, data_count: int):
    
    #Data Preparation
    age_groups, compensation_remote, compensation_hybrid = ['Under 25', '25-35', '35-45', '45-55', '55+'], [], []
    for doc in data:
        # data for the chart        
        if doc['RemoteWork'] == "Fully remote":
            compensation_remote.append(doc['AvgCompensation'])
        else:
            compensation_hybrid.append(doc['AvgCompensation'])    

    # set up the figure and axes
    fig, ax = plt.subplots(figsize=(10, 6))

    # plot the data
    bar_width = 0.35
    opacity = 0.8
    index = np.arange(len(age_groups))

    ax.bar(index, compensation_remote, bar_width, alpha=opacity, color='b', label='Fully remote')

    ax.bar(index + bar_width, compensation_hybrid, bar_width, alpha=opacity, color='g', label='Hybrid')

    # add labels and title
    ax.set_xlabel('Age groups')
    ax.set_ylabel('Average Compensation')
    ax.set_title('Average Compensation by Age group and Remote Work preference')
    ax.set_xticks(index + bar_width / 2)
    ax.set_xticklabels(age_groups)
    ax.legend()

    # display the chart
    plt.show()
    
    return

def plot_analyze_result_5(data: collection.Collection, data_count: int):

    table = PrettyTable()
    table.field_names = ["Job Title", "Years of Exp", "Compensation", "Top Languages"]
    temp = []
    for i in data:
        temp.append(i)    

    for d in temp:
        top_languages = ""
        for language in d['TopLanguages']:
            top_languages += language['Language'] + " (" + str(language['count']) + "), "
        top_languages = top_languages.rstrip(", ")
        
        # Add the data row to the table
        table.add_row([d['JobTitle'], d['YearsOfExp'], d['Compensation'], top_languages])

    # Print the table
    print(table)

    return

if __name__ == "__main__":

    #Get the database
    stack_db = get_database()

    #Get the collection
    stack_data = stack_db["surveyresult"]

    #Count of total data.
    data_count = stack_data.count_documents({})    
    # print("Data Count => ", data_count, "\n")

    #Analyze 1: Impact on Mental Health    
    # analyze_result_1 = analyze_mental_health_impact(stack_data, data_count)
    # plot_analyze_result_1(analyze_result_1, data_count)
    # print("\n")

    # #Analyze 2: Tech Stack Preference
    # analyze_result_2 = analyze_tech_stack_preference(stack_data, data_count)    
    # plot_analyze_result_2(analyze_result_2, data_count)
    # print("\n")

    # #Analyze 3: Percentage of Self Taught vs Traditional Learning that landed full time job as developer    
    # analyze_result_3 = employed_vs_unemployed_gap(stack_data, data_count)
    # plot_analyze_result_3(analyze_result_3, data_count)
    # print("\n")

    # # #Analyze 4: Impact of Remote Work on Age Group    
    # analyze_result_4 = analyze_remote_work_impact(stack_data, data_count)
    # plot_analyze_result_4(analyze_result_4, data_count)
    # print("\n")    

    # #Analyze 5: Most Common Languages used across each job title    
    analyze_result_5 = job_title_and_common_lang_used(stack_data, data_count)
    plot_analyze_result_5(analyze_result_5, data_count)
    print("\n")