import datetime
import time
import os
from pprint import pprint

import requests
from dotenv import load_dotenv

load_dotenv()
WEBHOOK = os.getenv('WEBHOOK')

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


def get_tasks_for_deal(deal_id=None, start=0) -> list or str:
    """Функция получает информацию о всех незавершенных задачах в сделке"""
    try:
        all_task_id = []
        params = {
            'start': start,
            'select': ['ID', 'TITLE', 'STATUS'],
            'filter': {
                'UF_CRM_TASK': f"D_{deal_id}"
            }
        }
        task_response = requests.post(WEBHOOK + 'tasks.task.list', json=params)
        if task_response.status_code != 200:
            time.sleep(2)
            task_response = requests.post(WEBHOOK + 'tasks.task.list', json=params)
        task_pagination = task_response.json()['total']
        if task_pagination < 50:
            all_task_id.extend(task_response.json()['result']['tasks'])
        else:
            while start < task_pagination:
                # page_count += 50
                # params.update({'start': page_count})
                start+=50
                new_task_response = requests.post(WEBHOOK + 'tasks.task.list', json=params)
                if new_task_response.status_code != 200:
                    time.sleep(2)
                    new_task_response = requests.post(WEBHOOK + 'tasks.task.list', json=params)
                all_task_id.extend(new_task_response.json()['result']['tasks'])
        return all_task_id
    except Exception as ex:
        return f'Ошибка при выполнении запроса', ex


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
                stat = task['status']
                if task['status'] in active_statuses:
                    break
            else:
                create_bitrix_task(deal_id)
                print(f'Создание новой задачи для сделки {deal_id} с завершенными задачами')


if __name__ == '__main__':
    # print(get_tasks_for_deal(deal_id=60299))
    main()
    print(
        f'Проведена проверка отсутствия задач в активных сделках Битрикса от {datetime.datetime.today().strftime("%d.%m.%Y")}')
