import httpx
import asyncio
import time
import pandas as pd
import datetime

base_url = 'https://portaldas.claro.com.ec:12900/oc/u-route/'


def login_action(username, password):
    encry_url = "SMLoginAction/getLoginRandomValue"
    login_url = "SMAuthenticateAction/authenticatelogin"

    encry_data = {"model": None, "params": {}}
    try:
        encry_res = httpx.request("POST", base_url + encry_url, json=encry_data)
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout):
        return -1, "Connection error"
    if encry_res.status_code != 200:
        return -1, encry_res.status_code
    random_value, login_cookies = encry_res.json(), encry_res.headers['set-cookie']

    login_data = {
        "model": None,
        "params": {
            "loginparam": {
                "userName": username,
                "password": f"[unencrypted][{random_value}]{password}",
            }
        }
    }

    login_headers = {
        'Content-Type': 'application/ueefire',
        'Cookie': login_cookies
    }

    login_res = httpx.request("POST", base_url + login_url, headers=login_headers, json=login_data)
    if login_res.status_code != 200:
        return -1, login_res.status_code
    if not login_res.json()['success']:
        return False, login_res.json()['errorMsg']
    return (True, {'JESSIONID': login_res.cookies.get('JSESSIONID'),
                   'u-token': login_res.cookies.get('u-token'),
                   'sna_cookie': login_res.cookies.get('bes_sna_cookie')})


def is_session_active(jssesionid='', u_token='', bes_sna_cookie=''):
    is_session_active_url = base_url + 'SMLoginActionCtz/querySessionIsActive'
    data = {"model": None, "params": {}}
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        'Cookie': f"JSESSIONID={jssesionid}; u-token={u_token}; bes_sna_cookie={bes_sna_cookie}",
        'u-token': f"{u_token}"
    }

    res = httpx.post(is_session_active_url, json=data, headers=headers)

    return res.status_code == 200


async def aquery_client(async_client: httpx.AsyncClient, login_res, phone_number=None, email=None, id_number=None,
                        imei=None, imsi=None, sim_card=None, first_name=None, second_last_name=None, last_name=None,
                        birthday=None, acct_code=None, acct_id=None, cust_id=None, begin_row_num=1,
                        fetch_row_num=10, include_history=False):
    if (phone_number is None and email is None and id_number is None
            and imei is None and imsi is None and sim_card is None and first_name is None and second_last_name is None
            and last_name is None and birthday is None and acct_code is None and acct_id is None and cust_id is None):
        raise Exception("At least one parameter must be provided")
    query_url = base_url + 'ucec/v1/ctz/queryoverseascustlist'
    data = {
        "model": None,
        "params": {
            "req": {
                "msisdn": phone_number,
                "email": email,
                "idNumber": id_number,
                "imei": imei,
                "isDeactivate": include_history,
                "imsi": imsi,
                "simCard": sim_card,
                "firstName": first_name,
                "secondLastName": second_last_name,
                "lastName": last_name,
                "birthday": birthday,
                "acctCode": acct_code,
                "acctId": acct_id,
                "custId": cust_id,
                "beginRowNum": begin_row_num,
                "fetchRowNum": fetch_row_num
            }
        }
    }
    headers = {
        "Content-Type": "application/ueefire",
        'Accept': 'application/json, text/plain, */*',
        'Cookie': f"JSESSIONID={login_res['JESSIONID']}; u-token={login_res['u-token']}; bes_sna_cookie={login_res['sna_cookie']}",
        'u-token': f"{login_res['u-token']}"
    }
    res = await async_client.post(query_url, json=data, headers=headers)
    res.raise_for_status()
    return data, res


async def aget_service_by_custid(async_client: httpx.AsyncClient, login_res, custId, subsId):
    url = base_url + 'ucec/v1/overseascustview/qryallsubsbycustid'
    data = {"model": None, "params": {"custId": custId, "beId": 101, "qryHistory": "N", "firstSubsId": subsId}}

    headers = {
        "Content-Type": "application/ueefire",
        'Accept': 'application/json, text/plain, */*',
        'Cookie': f"JSESSIONID={login_res['JESSIONID']}; u-token={login_res['u-token']}; bes_sna_cookie={login_res['sna_cookie']}",
        'u-token': f"{login_res['u-token']}"
    }
    res = await async_client.post(url, json=data, headers=headers)
    res.raise_for_status()
    return data, res


async def aget_consumo_by_service_number(async_client: httpx.AsyncClient, login_res, serviceNumber, TS_dateFrom,
                                         TS_dateTo, beginNumReq=0, fetchNumReq=0):
    consumos_url = base_url + 'querysubscriberallcdrboservice/querysubscriberallcdr'
    data = {
        "model": None,
        "params": {
            "header": {},
            "body": {
                "serviceNumber": serviceNumber,
                "dateFrom": TS_dateFrom,
                "dateTo": TS_dateTo,
                "beginNumReq": beginNumReq,
                "fetchNumReq": fetchNumReq,
                "totalNumReq": 0,
                "subsId": ""
            }
        }
    }

    headers = {
        "Content-Type": "application/ueefire",
        'Accept': 'application/json, text/plain, */*',
        'Cookie': f"JSESSIONID={login_res['JESSIONID']}; u-token={login_res['u-token']}; bes_sna_cookie={login_res['sna_cookie']}",
        'u-token': f"{login_res['u-token']}"
    }

    res = await async_client.post(consumos_url, json=data, headers=headers, timeout=60)
    res.raise_for_status()
    return data, res


async def query_clients(async_client: httpx.AsyncClient, login_res, client_info_list: list, info_type: str):
    if info_type not in ['phone_number', 'email', 'id_number', 'imei', 'imsi', 'sim_card', 'first_name',
                         'second_last_name', 'last_name', 'birthday', 'acct_code', 'acct_id', 'cust_id']:
        raise Exception("Invalid info_type")

    requests = [aquery_client(async_client, login_res, **{info_type: client_info}) for client_info in
                client_info_list]
    responses = await asyncio.gather(*requests)
    return responses


async def get_services_by_custid(async_client: httpx.AsyncClient, login_res, custIds: list, subsIds: list):
    if len(custIds) != len(subsIds):
        raise Exception("custIds and subsIds must have the same length")
    requests = [aget_service_by_custid(async_client, login_res, custIds[i], subsIds[i]) for i in range(len(custIds))]
    responses = await asyncio.gather(*requests)
    return responses


async def get_consumos_by_service_number(async_client: httpx.AsyncClient, login_res, serviceNumbers: list,
                                         TS_datesFrom: list, TS_datesTo: list, beginNumsReq: list = (),
                                         fetchNumsReq: list = ()):
    if len(serviceNumbers) != len(TS_datesFrom) or len(serviceNumbers) != len(TS_datesTo):
        raise Exception("serviceNumbers, TS_datesFrom and TS_datesTo must have the same length")
    if len(beginNumsReq) == 0:
        beginNumsReq = [0 for _ in range(len(serviceNumbers))]
    elif len(beginNumsReq) != len(serviceNumbers):
        raise Exception("beginNumsReq must have the same length as serviceNumbers")
    if len(fetchNumsReq) == 0:
        fetchNumsReq = [0 for _ in range(len(serviceNumbers))]
    elif len(fetchNumsReq) != len(serviceNumbers):
        raise Exception("fetchNumsReq must have the same length as serviceNumbers")

    requests = [
        aget_consumo_by_service_number(async_client, login_res, serviceNumbers[i], TS_datesFrom[i], TS_datesTo[i],
                                       beginNumsReq[i], fetchNumsReq[i]) for i in range(len(serviceNumbers))]
    responses = await asyncio.gather(*requests)
    return responses


def parse_query_client(responses: list | tuple):
    clients_info = []
    for client_res in responses:
        try:
            cust = client_res[1].json()['customerList'][0]
        except (TypeError, KeyError):
            cust = None

        simCard = client_res[0]['params']['req']['simCard']
        custId = cust['custId'] if client_res[1].json() else None
        subsId = cust['dftSubsId'] if client_res[1].json() else None
        client_info = {'custId': custId, 'subsId': subsId, 'simCard': simCard}
        clients_info.append(client_info)
    return clients_info


def parse_service_by_custid(responses: list | tuple):
    serviceNumbers = []
    for service_res in responses:
        try:
            json_query = service_res[1].json()['subsInfoList'][0]['subscriberBasic'] if service_res[1].json() else None
            serviceNumber = json_query['serviceNumber'] if service_res[1].json() else None
            activationDate = json_query['activeDate'] if service_res[1].json() else None
            service_dict = {'serviceNumber': serviceNumber, 'activationDate': activationDate}
        except (TypeError, KeyError):
            service_dict = {'serviceNumber': None, 'activationDate': None}
        service_dict.update({'subsId': service_res[0]['params']['firstSubsId']})
        serviceNumbers.append(service_dict)
    return serviceNumbers


# def parse_consumos_by_service(responses: list):
#

# function that that returns timestamps 30, 60, 90, 120, 150 and 180 days after the passed timestamp
def get_timestamps(timestamp: int | None):
    if timestamp is None:
        return [None for _ in range(6)]
    return [timestamp + i * 2592000 for i in range(1, 7)]


def get_sc_state(activationDate):
    current_ts = datetime.datetime.now().timestamp() * 1000
    if pd.isna(activationDate):
        return 0
    time_since_activation = (current_ts - activationDate) / 1000

    if time_since_activation < 30 * 86400:
        return 1
    elif time_since_activation < 60 * 86400:
        return 30
    elif time_since_activation < 90 * 86400:
        return 60
    elif time_since_activation < 120 * 86400:
        return 90
    elif time_since_activation < 150 * 86400:
        return 120
    elif time_since_activation < 180 * 86400:
        return 150
    else:
        return 180


def parse_consumos(consumos_res, n=30):
    consumos = []
    for i, consumo in enumerate(consumos_res):
        serviceNumber = consumo[0]['params']['body']['serviceNumber']
        summ = 0
        try:
            cdr_summary = consumo[1].json()['body']['cdrSummary']
        except (KeyError, TypeError):
            print('consumo', i)
            cdr_summary = []
        for summary in cdr_summary:
            summ = summ + summary['summaryTotalChargeInfoList'][0]['actualChargeAmt']
        consumos.append({'serviceNumber': serviceNumber, f'Consumo_{n}': summ})
    return consumos


async def fill_consumos(login_res, simc_df) -> pd.DataFrame:
    previous_state = 'activationDate'
    client = httpx.AsyncClient()
    for state in [30, 60, 90, 120, 150, 180]:
        date_upper_col = f'TS_{state}'
        for_state = simc_df.loc[
            simc_df['state'] >= state, [previous_state, date_upper_col, 'serviceNumber', 'state']]
        if not for_state.shape[0]: break
        cosmos_state = await get_consumos_by_service_number(
            client, login_res, for_state['serviceNumber'].to_list(), for_state[previous_state].to_list(),
            for_state[date_upper_col].to_list())
        previous_state = date_upper_col
        cosmos_state = parse_consumos(cosmos_state, n=state)
        cosmos_state = pd.DataFrame(cosmos_state)
        simc_df = pd.merge(simc_df, cosmos_state, on='serviceNumber', how='outer')
        time.sleep(2)
    await client.aclose()
    return simc_df


async def fill_crm_info(base_df: pd.DataFrame, login_res) -> pd.DataFrame:
    aclient = httpx.AsyncClient()
    query_by = (base_df['base'].astype(str) + base_df['serie'].astype(str)).to_list()
    query_res_ls = await (query_clients(aclient, login_res[1], query_by, 'sim_card'))
    query_df = pd.DataFrame(parse_query_client(query_res_ls))  # custId, subsId, simCard

    services_res = await (
        get_services_by_custid(aclient, login_res[1], query_df['custId'].to_list(), query_df['subsId'].to_list()))
    services_df = pd.DataFrame(parse_service_by_custid(services_res))
    timestamps_df = services_df['activationDate'].apply(lambda x: get_timestamps(x))
    timestamps_df = pd.DataFrame(timestamps_df.to_list(),
                                 columns=['TS_30', 'TS_60', 'TS_90', 'TS_120', 'TS_150', 'TS_180'], dtype='Int64')
    services_df['activationDate'] = services_df['activationDate'].fillna(0).astype(
        'int64')  # serviceNumber, activationDate, subsId

    simcard_df = pd.merge(pd.concat([services_df, timestamps_df], axis=1), query_df, on='subsId')[
        ['simCard', 'serviceNumber', 'custId', 'subsId', 'activationDate', 'TS_30', 'TS_60', 'TS_90', 'TS_120',
         'TS_150', 'TS_180']].drop_duplicates()
    simcard_df.loc[simcard_df['activationDate'] == 0, 'activationDate'] = simcard_df['TS_30']

    simcard_df['state'] = simcard_df['activationDate'].apply(lambda x: get_sc_state(x))
    simcard_df.to_csv("ENERO1_SIMCARD.csv", index=False)
    consumo_df = await fill_consumos(login_res[1], simcard_df)

    return consumo_df
