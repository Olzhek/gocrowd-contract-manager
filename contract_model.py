from dateutil.relativedelta import relativedelta
from datetime import date, timedelta
from helpers import shift_to_working_day, get_kz_holidays

class Contract :
    def __init__(self, name, principal, interest_rate, duration_months, start_date, repayment_start_month) :
        self.name = name
        self.principal = principal
        self.interest_rate = interest_rate
        self.duration_months = duration_months
        self.start_date = start_date
        self.repayment_start_month = repayment_start_month

        self.monthly_interest_rate = interest_rate / 12
        self.monthly_principal_payment = (
            principal / (duration_months - repayment_start_month + 1) if repayment_start_month <= duration_months else 0
        )

        self.schedule = self.generate_schedule()

    def generate_schedule(self) :
        schedule = []
        remaining_principal = self.principal
        for month in range(1, self.duration_months + 1) :
            raw_date = self.start_date + relativedelta(months=month)
            payment_date = shift_to_working_day(raw_date, get_kz_holidays())
            interest_payment = remaining_principal * self.monthly_interest_rate
            principal_payment = self.monthly_principal_payment if month >= self.repayment_start_month else 0
            total_payment = interest_payment + principal_payment

            schedule.append({
                "month": month,
                "date": payment_date,
                "interest": round(interest_payment, 2),
                "principal": round(principal_payment, 2),
                "total": round(total_payment, 2),
                "remaining_principal": round(remaining_principal - principal_payment, 2)
            })

            remaining_principal -= principal_payment

        return schedule

    def total_interest(self) :
        return round(sum(p["interest"] for p in self.schedule), 2)

    def total_payment(self) :
        return round(sum(p["total"] for p in self.schedule), 2)

    def get_schedule(self) :
        return self.schedule

    def is_active(self, today=None) :
        today = today or date.today()
        end_date = self.start_date + relativedelta(months=self.duration_months)
        return self.start_date <= today < end_date
    
    def to_dict(self) :
        return {
            "name": self.name,
            "principal": self.principal,
            "interest_rate": self.interest_rate,
            "duration_months": self.duration_months,
            "start_date": self.start_date.isoformat(),
            "repayment_start_month": self.repayment_start_month
        }
    
    @classmethod
    def from_dict(cls, data) :
        from datetime import date
        from dateutil.parser import parse

        return cls(
            name = data["name"],
            principal = data["principal"],
            interest_rate = data["interest_rate"],
            duration_months = data["duration_months"],
            start_date = parse(data["start_date"]).date(),
            repayment_start_month=data["repayment_start_month"]
        )
    
    def summary(self) :
        return {
            "name": self.name,
            "principal": self.principal,
            "interest_rate": self.interest_rate*100,
            "start_date": self.start_date.isoformat(),
            "duration_months": self.duration_months,
            "repayment_start_month": self.repayment_start_month,
            "total_interest": self.total_interest(),
            "total_payment": self.total_payment()
        }