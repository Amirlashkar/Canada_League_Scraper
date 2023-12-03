from datetime import datetime

date_string = "December 1, 2023"
date_format = "%B %d, %Y"
date_format1 = "%m-%d-%Y"

datetime_obj = datetime.strptime(date_string, date_format)
datetime_obj = datetime_obj.strftime(date_format1)
print(datetime_obj)
