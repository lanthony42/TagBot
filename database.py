import os
from utils import debug
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import AuthorizedSession


class Database:
    def __init__(self, key: str):
        scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/spreadsheets',
                  'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
        directory_path = os.path.dirname(os.path.abspath(__file__))
        new_path = os.path.join(directory_path, 'credentials.json')
        credentials = ServiceAccountCredentials.from_json_keyfile_name(new_path, scopes)
        data = credentials.serialization_data
        data['token_uri'] = credentials.token_uri

        auth = Credentials.from_service_account_info(data, scopes=scopes)
        self.session = AuthorizedSession(auth)
        self.id = key

        self.fetched_data = {}
        self.requests = []

    def fetch(self) -> bool:
        response = self.session.get(f'https://sheets.googleapis.com/v4/spreadsheets/{self.id}',
                                    params={'fields': 'sheets.data.rowData.values.userEnteredValue,'
                                                      'sheets.properties.sheetId,'
                                                      'sheets.properties.title'})
        self.fetched_data = {}

        if not response.ok:
            debug(f'API ERROR: {response.text}')
            return False

        data = response.json()
        for sheet in data['sheets']:
            values = [[list(value['userEnteredValue'].values())[0] if value else '' for value in row['values']]
                      if row else [] for row in sheet['data'][0]['rowData']]

            item = {'sheetId': sheet['properties']['sheetId'], 'data': fill_gaps(values)}
            self.fetched_data[sheet['properties']['title']] = item
        return True

    def push(self) -> list:
        if self.requests:
            response = self.session.post(f'https://sheets.googleapis.com/v4/spreadsheets/{self.id}:batchUpdate',
                                         json={'requests': self.requests})
            self.requests = []

            if response.ok:
                return response.json()['replies']
            else:
                debug(f'API ERROR: {response.text}')
        return []

    # Add to database
    def add_record(self, sheet_name: str, record: dict) -> list:
        """ Adds record to database.

        :param sheet_name: Name of worksheet to add to
        :param record: Record (as a dictionary) to add
        :return: List representing added record
        """
        row_data = []
        fields = self.fetched_data[str(sheet_name)]['data'][0]

        for field in fields:
            if field in record.keys():
                row_data.append({'userEnteredValue': {'stringValue': str(record[field])}})
            else:
                row_data.append({})

        clean_record = [list(value['userEnteredValue'].values())[0] if value else '' for value in row_data]
        self.fetched_data[str(sheet_name)]['data'].append(clean_record)

        request = {'appendCells': {'sheetId': int(self.fetched_data[str(sheet_name)]['sheetId']),
                                   'rows': [{'values': row_data}],
                                   'fields': 'userEnteredValue'}
                   }
        self.requests.append(request)
        return clean_record

    def duplicate_sheet(self, sheet_id: int, new_name: str, new_index: int = 1) -> None:
        request = {'duplicateSheet': {'sourceSheetId': int(sheet_id),
                                      'insertSheetIndex': int(new_index),
                                      'newSheetName': str(new_name)}
                   }
        self.requests.append(request)

    # Clears values from database
    def clear(self):
        for sheet_title in self.fetched_data.keys():
            sheet_id = self.fetched_data[sheet_title]['sheetId']
            self.clear_sheet(sheet_id)

    def clear_record(self, sheet_name: str, field: str, key: str):
        row = search_row_index(self.fetched_data[str(sheet_name)]['data'], {field: key})

        if row:
            request = {'updateCells': {'fields': 'userEnteredValue',
                                       'range': {'sheetId': int(self.fetched_data[str(sheet_name)]['sheetId']),
                                                 'startRowIndex': row,
                                                 'endRowIndex': row + 1}
                                       }
                       }
            self.requests.append(request)
            return True
        else:
            debug('Item not found!')
        return False

    def clear_sheet(self, sheet_id: int):
        request = {'updateCells': {'fields': 'userEnteredValue',
                                   'range': {'sheetId': int(sheet_id),
                                             'startRowIndex': 1}
                                   }
                   }
        self.requests.append(request)

    # Delete from database
    def del_record(self, sheet_name: str, field: str, key: str):
        row = search_row_index(self.fetched_data[sheet_name]['data'], {field: key})

        if row:
            self.del_row(self.fetched_data[sheet_name]['sheetId'], row)
            return True
        else:
            debug('Item not found!')
        return False

    def del_row(self, sheet_id: int, row: int):
        request = {'deleteRange': {'range': {'sheetId': int(sheet_id),
                                             'startRowIndex': row,
                                             'endRowIndex': row + 1},
                                   'shiftDimension': 'ROWS'
                                   }
                   }
        self.requests.append(request)

    def del_sheet(self, sheet_id: int):
        request = {'deleteSheet': {'sheetId': int(sheet_id)}}
        self.requests.append(request)

    # Get from database
    def get_item(self, sheet_name: str, key_field: str, key: str, field: str):
        data = self.fetched_data[sheet_name]['data']
        rows = query_values_for_row(data, {key_field: key})

        if rows:
            col = search_field_index(data, field)
            output = [record[col] for record in rows]
            return output  # if len(output) > 1 else output[0]
        else:
            debug('Items not found!')
        return None

    def get_record(self, sheet_name: str, field: str, key: str):
        data = self.fetched_data.get(sheet_name)['data']
        row = query_values_for_row(data, {field: key})
        if row:
            record_dicts = [record_to_dict(data, record) for record in row]
            return record_dicts  # if len(record_dicts) > 1 else record_dicts[0]
        else:
            debug('Item not found!')
        return None

    # Updates database
    def update_item(self, sheet_id: int, data: list, key_field: str, key: str, field: str, item: str):
        row = search_row_index(data, {key_field: key})

        if row:
            col = search_field_index(data, field)
            request = {'updateCells': {'rows': [{'values': [{'userEnteredValue': {'stringValue': str(item)}}]}],
                                       'fields': 'userEnteredValue',
                                       'start': {'sheetId': int(sheet_id),
                                                 'rowIndex': row,
                                                 'columnIndex': col}
                                       }
                       }
            self.requests.append(request)
            return True
        else:
            debug('Item not found!')
        return False

    def update_record(self, sheet_name: str, field: str, key: str, record: dict):
        row_data = []
        fields = self.fetched_data[str(sheet_name)]['data'][0]

        for col in fields:
            if col in record.keys():
                row_data.append({'userEnteredValue': {'stringValue': str(record[col])}})
            else:
                row_data.append({})

        row = search_row_index(self.fetched_data[str(sheet_name)]['data'], {field: key})
        if row:
            request = {'updateCells': {'rows': [{'values': row_data}],
                                       'fields': 'userEnteredValue',
                                       'range': {'sheetId': int(self.fetched_data[str(sheet_name)]['sheetId']),
                                                 'startRowIndex': row,
                                                 'endRowIndex': row + 1}
                                       }
                       }
            self.requests.append(request)
            return True
        else:
            debug('Item not found!')
        return False


# Code used from gspread by Anton Burnashev
def fill_gaps(data: list, rows=None, cols=None):
    max_cols = max(len(row) for row in data) if cols is None else cols
    max_rows = len(data) if rows is None else rows

    pad_rows = max_rows - len(data)

    if pad_rows:
        data = data + ([[]] * pad_rows)

    def right_pad(row, max_len):
        pad_len = max_len - len(row)
        return row + ([''] * pad_len) if pad_len != 0 else row

    return [right_pad(row, max_cols) for row in data]


def get_item(data: list, key_field: str, key: str, field: str):
    rows = query_values_for_row(data, {key_field: key})
    if rows:
        col = search_field_index(data, field)
        output = [record[col] for record in rows]
        return output if len(output) > 1 else output[0]
    else:
        debug('Item not found!')
        return None


def get_all_items(data: list, field: str):
    col = search_field_index(data, field)
    output = [record[col] for record in data]
    return output if len(output) > 1 else output[0]


def prepare_record(data: list, **kwargs):
    output = {}
    fields = data[0]

    for field in fields:
        if field in kwargs.keys():
            output[field] = kwargs[field]
    return output


def query_values_for_row(data: list, query: dict):
    fields = data[0]
    output = data[1:]

    for key in query.keys():
        for row in list(output):
            if str(row[fields.index(key)]) != str(query[key]):
                output.remove(row)
    return output


def record_to_dict(data: list, record: dict):
    fields = data[0]
    return {field: record[index] for index, field in enumerate(fields)}


# Search for index functions are all 0-indexed (since Database Update 0.3)
def search_row_index(data: list, query: dict):
    fields = data[0]

    for i in range(1, len(data)):
        for key in query.keys():
            if str(data[i][fields.index(key)]) != str(query[key]):
                break
            return i
    return None


def search_field_index(data: list, field: str):
    return data[0].index(str(field))
