from pprint import pprint
import csv
import re

# -----------------------------------------------------------
# читаем адресную книгу в формате CSV в список contacts_list
# -----------------------------------------------------------
with open("phonebook_raw.csv", encoding="utf-8") as f:
    rows = csv.reader(f, delimiter=",")
    contacts_list = list(rows)

print("=== ДО ОБРАБОТКИ ===")
pprint(contacts_list)


# -----------------------------------------------------------
# TODO 1: Выполняем пункты 1-3 ДЗ
# -----------------------------------------------------------

def clean_name(row):
    """
    Разделяет Фамилию, Имя и Отчество из первых трёх полей строки.
    Поддерживаемые форматы:
      - Ф, И, О         (уже разделено, всё заполнено)
      - Ф, ИО           (имя и отчество вместе через пробел)
      - Ф, И            (только имя, без отчества)
      - Ф, И,           (имя есть, отчество пустое)
      - Ф, ИО,          (имя+отчество вместе, третье поле пустое)
    """
    parts = [p.strip() for p in row[:3]]
    # Дополняем пустыми строками, если меньше 3 элементов
    while len(parts) < 3:
        parts.append("")

    lastname = parts[0]
    firstname = parts[1]
    surname = parts[2]

    # Если surname пустое, а в firstname есть пробел — это "Имя Отчество"
    if not surname and " " in firstname:
        name_parts = firstname.split()
        firstname = name_parts[0]
        surname = name_parts[1] if len(name_parts) > 1 else ""

    return [lastname, firstname, surname]


def normalize_phone(raw_phone):
    """
    Приводит телефон к формату +7(999)999-99-99 доб.XXXX
    """
    if not raw_phone:
        return ""

    raw_phone = raw_phone.strip()

    # Извлекаем расширение (добавочный номер)
    extension = ""
    ext_match = re.search(
        r'(?:доб\.?|ext\.?|add\.?)[\s:]*([\d]+)',
        raw_phone, re.IGNORECASE
    )
    if ext_match:
        extension = "доб." + ext_match.group(1)
        phone_only = raw_phone[:ext_match.start()].strip()
    else:
        phone_only = raw_phone

    # Оставляем только цифры и возможный плюс в начале
    phone_digits = re.sub(r'[^\d+]', '', phone_only)

    # Проверяем российский номер: +7 или 8, затем 10 цифр
    match = re.match(r'^(\+?7|8)(\d{10})$', phone_digits)
    if match:
        digits = match.group(2)
        formatted = f"+7({digits[0:3]}){digits[3:6]}-{digits[6:8]}-{digits[8:10]}"
        if extension:
            formatted += f" {extension}"
        return formatted

    # Если не удалось распознать — возвращаем исходный номер
    return raw_phone


def merge_contacts(contacts):
    """
    Объединяет дублирующиеся записи.
    Критерий дублирования: совпадают Фамилия и Имя (без учёта регистра).
    Объединяем все уникальные телефоны и email'ы.
    """
    groups = {}   # key: (lastname_lower, firstname_lower) -> dict
    order = []     # порядок первого появления

    for row in contacts:
        # Дополняем строку до 7 полей, если не хватает
        while len(row) < 7:
            row.append("")

        # Очищаем ФИО
        cleaned = clean_name(row)
        lastname, firstname, surname = cleaned

        organization = row[3].strip()
        position = row[4].strip()
        phones_raw = row[5].strip()
        emails_raw = row[6].strip()

        # Ключ для группировки — Фамилия + Имя (регистронезависимый)
        key = (lastname.lower().strip(), firstname.lower().strip())

        if key not in groups:
            groups[key] = {
                "lastname": lastname,
                "firstname": firstname,
                "surname": surname,
                "organization": organization,
                "position": position,
                "phones": set(),
                "emails": set(),
            }
            order.append(key)
        else:
            entry = groups[key]
            # Обновляем поля, если текущие пустые, а новые — заполнены
            if not entry["surname"] and surname:
                entry["surname"] = surname
            if not entry["organization"] and organization:
                entry["organization"] = organization
            if not entry["position"] and position:
                entry["position"] = position

        # Добавляем телефоны
        if phones_raw:
            for p in phones_raw.split(","):
                p = p.strip()
                if p:
                    groups[key]["phones"].add(p)

        # Добавляем email'ы
        if emails_raw:
            for e in emails_raw.split(","):
                e = e.strip()
                if e:
                    groups[key]["emails"].add(e)

    # Формируем итоговый список
    merged = []
    for key in order:
        entry = groups[key]

        # Нормализуем все телефоны
        phones_normalized = []
        seen_phones = set()
        for p in sorted(entry["phones"]):
            normalized = normalize_phone(p)
            if normalized and normalized not in seen_phones:
                phones_normalized.append(normalized)
                seen_phones.add(normalized)

        emails = sorted(entry["emails"])

        row = [
            entry["lastname"],
            entry["firstname"],
            entry["surname"],
            entry["organization"],
            entry["position"],
            ",".join(phones_normalized),
            ",".join(emails),
        ]
        merged.append(row)

    return merged


# -----------------------------------------------------------
# Применяем обработку
# -----------------------------------------------------------
contacts_list = merge_contacts(contacts_list)

print("\n=== ПОСЛЕ ОБРАБОТКИ ===")
pprint(contacts_list)


# -----------------------------------------------------------
# TODO 2: Сохраняем результат в файл phonebook.csv
# -----------------------------------------------------------
with open("phonebook.csv", "w", encoding="utf-8", newline='') as f:
    datawriter = csv.writer(f, delimiter=',')
    datawriter.writerows(contacts_list)

print("\nФайл phonebook.csv успешно сохранён.")
