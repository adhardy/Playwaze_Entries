import pandas as pd
import numpy as np
from typing import List, Union

# column names for reports for convenience in code. The strings should match that in the playwaze config file.
COL_CREW_ID = "crew id"
COL_BOAT_TYPE = "boat type"
COL_CLUB = "club"
COL_CREW_NAME = "crew name"
COL_CREW_LETTER = "crew letter"
COL_SEATS = "seats"
COL_VERIFIED = "verified"
COL_CAPTAIN = "captain"
COL_CAPTAIN_NAME = "captain name"
COL_COX = "cox"
COL_COX_NAME = "cox name"
COL_MEMBER_ID =  "member id"
COL_NAME = "name"
COL_GENDER = "gender"
COL_DOB = "dob"
COL_SR_NUMBER = "sr member number"
COL_MEMBERSHIP_TYPE = "membership type"
COL_EXPIRY = "membership expiry"
COL_ROW_POINTS = "rowing points"
COL_ROW_NOVICE = "rowing novice"
COL_SCULL_POINTS = "sculling points"
COL_SCULL_NOVICE = "sculling novice"
COL_PRIMARY_CLUB = "primary club"
COL_ADDITIONAL_CLUBS = "additional clubs"
COL_FIRST_LICENCE = "first licence start date"
COL_COMPOSITE_CLUBS = "composite clubs"

TEAM_COLUMNS = [COL_CREW_ID, COL_BOAT_TYPE, COL_CLUB, COL_CREW_NAME, 
    COL_CREW_LETTER, COL_SEATS, COL_VERIFIED, COL_CAPTAIN,COL_CAPTAIN_NAME, COL_COX, COL_COX_NAME]

TEAM_MEMBER_COLUMNS = [COL_BOAT_TYPE, COL_CLUB, COL_CREW_ID, COL_CREW_LETTER, COL_CREW_NAME, COL_MEMBER_ID, 
    COL_NAME, COL_GENDER, COL_DOB, COL_SR_NUMBER, COL_MEMBERSHIP_TYPE,COL_EXPIRY,COL_ROW_POINTS,
    COL_ROW_NOVICE, COL_SCULL_POINTS, COL_SCULL_NOVICE, COL_PRIMARY_CLUB,COL_ADDITIONAL_CLUBS, COL_FIRST_LICENCE,COL_COMPOSITE_CLUBS]

COMMUNITY_MEMBER_COLUMNS = [COL_MEMBER_ID, COL_NAME, COL_DOB, COL_GENDER, COL_SR_NUMBER, 
    COL_MEMBERSHIP_TYPE, COL_EXPIRY, COL_ROW_POINTS, COL_ROW_NOVICE, COL_SCULL_POINTS, COL_SCULL_NOVICE, 
    COL_PRIMARY_CLUB, COL_ADDITIONAL_CLUBS, COL_FIRST_LICENCE, COL_COMPOSITE_CLUBS]

# additional columns we create
COL_POSITION = "position"

# file type of uploaded reports
REPORT_FILE_TYPE = "xlsx"


def cleanup_report_columns(df: pd.DataFrame, column_numbers: List[int], column_names: List[str]) -> pd.DataFrame:

    df = df.iloc[:,column_numbers] # keep only the columns we need
    df.columns = column_names # and rename them to match names in config

    return df


def clean_booleans(df: pd.DataFrame) -> pd.DataFrame:
    """Replaces Y, N and nan with True/False"""

    df = df.replace({"Y":True, np.nan:False, "N":False})
    return df.astype(bool)


def assign_rower_position(df):
    """Assign a unique position (number) to rowers in each crew"""

    df["position"] = df.groupby(COL_CREW_ID).cumcount()
    df["position"] = df["position"] + 1 # index from 1

    return df["position"].astype(str)


def get_coxes(df_teams: pd.DataFrame, df_team_members: pd.DataFrame, df_members: Union[None, pd.DataFrame] = None):
    """Get coxes from a Playwaze teams report, match their details from either a community members or team members report, and insert them into the team members dataframe"""

    # extract all coxes from the teams report
    df_coxes = df_teams.loc[df_teams[COL_COX]==True, [COL_COX_NAME, COL_CREW_ID, COL_CREW_NAME, COL_CREW_LETTER, COL_CLUB, COL_BOAT_TYPE]]
    df_coxes[COL_POSITION] = "C"
    df_coxes = df_coxes.rename(columns={COL_COX_NAME:COL_NAME}) # rename the name column to match the members df
    
    # try and find their membership number if they are entered as a rower in another crew
    # if a community members report is not included, get a list of rowers from the team members report
    if df_members is None:
        df_members = get_unique_rowers(df_team_members)

    # look up cox details from the members report
    df_coxes = pd.merge(
        df_coxes, 
        df_members[[COL_NAME, COL_SR_NUMBER, COL_GENDER, COL_DOB, COL_MEMBERSHIP_TYPE, COL_EXPIRY, COL_PRIMARY_CLUB, COL_ADDITIONAL_CLUBS, COL_FIRST_LICENCE, COL_COMPOSITE_CLUBS, COL_ROW_NOVICE, COL_SCULL_NOVICE, COL_ROW_POINTS, COL_SCULL_POINTS]], 
        left_on=[COL_NAME], 
        right_on=[COL_NAME], 
        how="left")

    # add coxes to the rowers dataframe
    df_team_members = df_team_members.append(df_coxes)

    # somewhere above, membership number gets turned to an interger, convert back to string
    df_team_members[COL_SR_NUMBER] = df_team_members[COL_SR_NUMBER].fillna(0) # remove NANs so can convert to string
    df_team_members[COL_SR_NUMBER] = df_team_members[COL_SR_NUMBER].astype(int).astype(str)
    df_team_members.loc[df_team_members[COL_SR_NUMBER] == "0", COL_SR_NUMBER] = np.nan # convet back to nan

    return df_team_members


def get_unique_rowers(df: pd.DataFrame):
    """Get a unique list of rowers from a Playwaze team members report"""

    df_rowers = df[df.duplicated(subset=[COL_NAME, COL_SR_NUMBER]) == False]
    return df_rowers