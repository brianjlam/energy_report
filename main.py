# python2.7
import csv
import numpy as np
from datetime import datetime


# Global parameters here
data_dir = "./data/"
summer_start = 5 # May 1
summer_end = 10 # Oct 31


def read_csv(month,filename):
    """Read DARS csv file into dictionary with keys from first row.

    output[point_time] is an array of strings
    All others are arrays of floats

    """
    path = data_dir + month + '/' + filename
    with open(path) as csvfile:
        reader = csv.reader(csvfile)

        row1 = next(reader) # generate list of keys
        keys = [key.strip() for key in row1]

        output = {} # initialize dict
        for key in keys:
            output[key] = []

        for row in reader: # add csv values to dict
            output[keys[0]].append(row[0].strip()) # first key always point_time
            for i in range(1,len(keys)):
                output[keys[i]].append(float(row[i].strip('$')))

        # for hourly data, check that beginning and end are 00:00 and 23:00
        # DARS uses the date format mm/dd/yyyy hh:mm:ss
        if '00:00:00' not in output[keys[0]][0] and 'hours' in filename:
            print('Warning: input file ' + filename + ' may be formatted incorrectly.')
        if '23:00:00' not in output[keys[0]][-1] and 'hours' in filename:
            print('Warning: input file ' + filename + ' may be formatted incorrectly.')
    return output


class Month():
    
    def __init__(self,month):
        self.billing_cycle_hours = read_csv(month,'billing_cycle_hours.CSV')
        self.month_hours         = read_csv(month,'month_hours.CSV')
        self.month_days          = read_csv(month,'month_days.CSV')
        self.rates               = read_csv(month, 'rates.CSV')

    def steam_cost(self):
        """Return the generation of steam in lb."""
        aux1 = sum(self.month_hours['F7424'])
        aux2 = sum(self.month_hours['F7425'])
        whb1 = sum(self.month_hours['F7421'])
        whb2 = sum(self.month_hours['F7422'])
        cogen= sum(self.month_hours['FS74409DUP'])
        return aux1,aux2,whb1,whb2,cogen

    def aux_eff(self):
        """Return the efficiency of aux boilers."""
        MMBtu_per_kcf_ng = 1.03
        MMBtu_per_kcf_lfg = 0.55
        MMBtu_per_lb_steam = 1194
        aux2_ng    = sum(self.month_hours['F7427DUP'])/24*MMBtu_per_kcf_ng 
        aux2_lfg   = sum(self.month_hours['F7428DUP'])/24*MMBtu_per_kcf_ng 
        aux1_ng    = sum(self.month_hours['F7431DUP'])/24*MMBtu_per_kcf_lfg
        aux1_lfg   = sum(self.month_hours['F7432DUP'])/24*MMBtu_per_kcf_lfg
        aux2_steam = sum(self.month_hours['F7425'])*MMBtu_per_lb_steam
        aux1_steam = sum(self.month_hours['F7424'])*MMBtu_per_lb_steam
        aux1_eff = (aux1_ng + aux1_lfg)/aux1_steam
        aux2_eff = (aux2_ng + aux2_lfg)/aux2_steam
        return aux1_eff, aux2_eff

    def cogen_ecost(self):
        """Return demand charge for the given month."""

        demand = self.billing_cycle_hours['PGEPWR']
        max_index = np.argmax(demand) 
        max_demand = np.max(demand) # kW
        time = self.billing_cycle_hours['point_time'][max_index]
        demand_rate, energy_rate = self.get_rate(time)
        demand_charge = demand_rate*max_demand

        demand_no_cogen = demand + self.billing_cycle_hours['COGENKW'] # needs work
        return demand_charge

    def get_rate(self,point_time):
        """Retrieves PG&E rate given datetime string."""
        print('Verify proper formatting of rates.CSV before using.')
        # time in format of mm/dd/yyyy hh:mm:ss
        time_obj = datetime.strptime(point_time, '%m/%d/%Y %H:%M:%S')
        hr = time_obj.hour
        # summer
        if time_obj.month >= summer_start and time_obj.month <= summer_end:
            demand_rate = self.rates['demand charge'][3] # base summer demand
            # weekday
            if time_obj.weekday() < 5: 
                if hr >= 12 and hr <= 18:
                    demand_rate += self.rates['demand charge'][0]
                    energy_rate = self.rates['energy charge'][0]
                elif hr > 8.5 and hr < 21.5:
                    demand_rate += self.rates['demand charge'][1]
                    energy_rate = self.rates['energy charge'][1]
                else:
                    demand_rate += self.rates['demand charge'][2]
                    energy_rate = self.rates['energy charge'][2]
            # weekend
            else:
                demand_rate += self.rates['demand charge'][2]
                energy_rate = self.rates['energy charge'][2]
        # winter  
        else: 
            demand_rate = self.rates['demand charge'][6] # base winter demand
            # weekday
            if time_obj.weekday() < 5: 
                if hr > 8.5 and hr < 21.5:
                    demand_rate += self.rates['demand charge'][4]
                    energy_rate = self.rates['energy charge'][4]
                else:
                    demand_rate += self.rates['demand charge'][5]
                    energy_rate = self.rates['energy charge'][5]
            # weekend
            else:
                demand_rate += self.rates['demand charge'][5]
                energy_rate = self.rates['energy charge'][5]
        return demand_rate, energy_rate


if __name__ == "__main__":
    dec17 = Month('dec17')
    print dec17.rates
    print dec17.cogen_ecost()

