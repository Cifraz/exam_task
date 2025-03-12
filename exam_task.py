import datetime
import time
from pprint import pprint

from infisical_base import infisical_get_secret
import requests

WEBHOOK = infisical_get_secret('WEBHOOK')


def get_all_deal_info() -> list or str or None:
    """ Получение ID всех незакрытых сделок"""
    try:
        all_deal_id = []
        page_count = 0
        data = {
            'select': ['ID'],
            'filter': {
                'CLOSED': 'N',
                'CATEGORY_ID': ['1', '11', '13', '15', '19', '29', '31', '35', '37']  # Все воронки Касымовой
            }
        }
        deals_response = requests.post(WEBHOOK + 'crm.deal.list', json=data)
        if deals_response.status_code != 200:
            time.sleep(2)
            deals_response = requests.post(WEBHOOK + 'crm.deal.list', json=data)
        total_pagination = deals_response.json()['total']
        all_deal_id.extend(deals_response.json()['result'])
        if total_pagination < 50:
            return all_deal_id
        else:
            while page_count < total_pagination:
                page_count += 50
                data.update({'start': page_count})
                new_deals_response = requests.post(WEBHOOK + 'crm.deal.list', json=data)
                if new_deals_response.status_code != 200:
                    time.sleep(2)
                    new_deals_response = requests.post(WEBHOOK + 'crm.deal.list', json=data)
                all_deal_id.extend(new_deals_response.json()['result'])
            return all_deal_id
    except Exception as ex:
        return f'Ошибка при выполнении запроса', ex


def get_tasks_for_deal(deal_id, start=0) -> list or str:
    """Функция получает информацию о всех незавершенных задачах в сделке"""
    all_task_id = []
    params = {
        'start': start,
        'select': ['ID', 'TITLE', 'STATUS', 'UF_CRM_TASK'],
        'filter': {'UF_CRM_TASK': f'd_{deal_id}'}
    }
    try:
        while True:
            task_response = requests.post(WEBHOOK + 'tasks.task.list', json=params)
            if task_response.status_code != 200:
                time.sleep(2)
                task_response = requests.post(WEBHOOK + 'tasks.task.list', json=params)
            task_data = task_response.json()
            if 'result' in task_data and 'tasks' in task_data['result']:
                all_task_id.extend(task_data['result']['tasks'])
            else:
                break
            task_pagination = task_data.get('total', 0)
            if len(all_task_id) >= task_pagination:
                break
            start += 50
            params['start'] = start
        return all_task_id
    except Exception as ex:
        return f'Ошибка при выполнении запроса: {ex}'


def get_task_by_id(task_id, webhook=WEBHOOK):
    """Функция находит задачу по ID"""
    url = f"{webhook}tasks.task.get"
    params = {"taskId": task_id,
              "select": {
                  'STATUS': 'STATUS',
                  'UF_CRM_TASK': 'UF_CRM_TASK'
              }
              }
    response = requests.post(url, json=params)
    result = response.json()
    return result


def assigned_user_info(deal_id) -> str or int:
    """ Функция определяющая ID пользователя, который ответственный за сделку"""
    assigned_by_id = requests.post(WEBHOOK + 'crm.deal.get', json={"ID": deal_id})
    if assigned_by_id.status_code != 200:
        time.sleep(2)
        assigned_by_id = requests.post(WEBHOOK + 'crm.deal.get', json={"ID": deal_id})
    return assigned_by_id.json()['result']['ASSIGNED_BY_ID']


def create_bitrix_task(deal_id: str or int):
    """ Функция создающая задачу в сделке Битрикса.
     На вход принимает ID сделки, номер папки для скачивания и, при наличии, текст дополнительного комментария"""
    try:
        responsible_user = assigned_user_info(deal_id)
        data = {'fields': {
            'TITLE': "Внимание! Активная сделка без задачи.",
            'DESCRIPTION': f"Поставьте актуальную задачу или завершите сделку",
            'STATUS': 2,
            'CREATED_BY': 1,
            'RESPONSIBLE_ID': int(responsible_user),
            'CREATED_DATE': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'DEADLINE': (datetime.datetime.now() + datetime.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
            'UF_CRM_TASK': [f'D_{deal_id}']
        }}
        response = requests.post(WEBHOOK + 'tasks.task.add', json=data)
        if response.status_code != 200:
            time.sleep(2)
            response = requests.post(WEBHOOK + 'tasks.task.add', json=data)
        return response.json()
    except Exception as ex:
        print('create_bitrix_task_os', ex)


def main():
    """ Функция запускающая проверку наличия задач в активных сделках Битрикса"""
    all_deals = get_all_deal_info()
    active_statuses = ['2', '3', '4', '6']  # Список активных статусов
    for deal in all_deals:
        deal_id = deal['ID']
        tasks = get_tasks_for_deal(deal_id=deal_id)

        if not tasks:
            create_bitrix_task(deal_id)
            print(f'Создание новой задачи для сделки {deal_id} где не было задач')
        else:
            for task in tasks:
                if task['status'] in active_statuses:
                    break
            else:
                create_bitrix_task(deal_id)
                print(f'Создание новой задачи для сделки {deal_id} с завершенными задачами')


if __name__ == '__main__':
    # for index, row in enumerate(get_tasks_for_deal(deal_id='60299')):  # 62933 60299
    #     if row['id'] == '167941':  # 150441
    #         pprint([index, row['id']])
    #     pprint([index, row['id'], row['status']])
    # pprint(get_task_by_id('167941'))
    # pprint(get_tasks_for_deal(deal_id='60299'))
    main()
    print(
        f'Проведена проверка отсутствия задач в активных сделках Битрикса от {datetime.datetime.today().strftime("%d.%m.%Y")}')
