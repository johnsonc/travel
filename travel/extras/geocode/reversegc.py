import os
import sys
import csv
from scipy.spatial import cKDTree as KDTree
if 1:
    try:
        from django.db.models import Q
        from travel.models import TravelEntity
    except ImportError:
        TravelEntity = None

# location of geocode data to download
GEOCODE_URL = 'http://download.geonames.org/export/dump/cities1000.zip'

def geo_loader():
    """Singleton pattern to avoid loading class multiple times
    """
    _instances = {}
    def _loader(cls_name, *args, **kws):
        
        cls = dict(csv=CSVGeocodeData, travel=TravelGeocodeData)[cls_name]
        key = (cls_name, args, tuple(kws.items()))
        if key not in _instances:
            _instances[key] = cls(*args, **kws)
        return _instances[key]
    return _loader
geo_loader = geo_loader()


def relative_path(fn):
    return os.path.join(os.path.dirname(__file__), fn)


class BaseGeocodeData(object):

    def __init__(self):
        self.coordinates, self.locations = self.extract()
        self.countries = self.load_countries()
        self.tree = self.load_tree(self.coordinates)
    
    def load_tree(self, coordinates):
        return KDTree(coordinates)
        
    def load_countries(self):
        raise NotImplementedError
    
    def extract(self):
        raise NotImplementedError
    
    def query(self, coordinates):
        """Find closest match to this list of coordinates
        """
        try:
            distances, indices = self.tree.query(coordinates, k=3)
        except ValueError as e:
            raise ValueError('Unable to parse coordinates: {}'.format(coordinates))

        #import ipdb; ipdb.set_trace()
        #print '***', type(indices), indices, list(indices)
        distances = distances.tolist()[0]
        indices = indices.tolist()[0]
        results = [self.locations[index] for index in indices]
        for i, result in enumerate(results):
            result['country'] = self.countries.get(result['co'], '')
            result['distance'] = distances[i]
        return results

    def get(self, coordinate):
        """Search for closest known location to this coordinate
        """
        return self.query([coordinate])[:3]

    def search(self, coordinates):
        """Search for closest known locations to these coordinates
        """
        return self.query(coordinates)


class TravelGeocodeData(BaseGeocodeData):

    def __init__(self, type_abbr=None):
        #type__abbr__in=['cn', 'lm']
        values = ('code', 'name', 'lat', 'lon', 'type__abbr', 'country__code')
        qs = TravelEntity.objects.filter(lat__isnull=False)
        if type_abbr:
            qs = qs.filter(type__abbr=type_abbr)
        
        self.entities = qs.values(*values)
        super(TravelGeocodeData, self).__init__()
        
    def load_countries(self):
        """Load a map of country code to name
        """
        countries = {}
        for e in self.entities:
            if e['type__abbr'] == 'co':
                e['country__code'] = e['code']
                countries[e['code']] = e['name']
        return countries

    def extract(self):
        coordinates, locations = [], []
        for e in self.entities:
            coordinates.append((e['lat'], e['lon']))
            locations.append(dict(
                code=e['code'],
                name=e['name'],
                type=e['type__abbr'],
                co=e['country__code']
            ))
            
        return coordinates, locations


class CSVGeocodeData(BaseGeocodeData):

    def __init__(self, geocode_filename='geocode.csv', country_filename='countries.csv'):
        csv.field_size_limit(sys.maxint)
        self.country_filename = relative_path(country_filename)
        self.geocode_filename = relative_path(geocode_filename)
        print self.country_filename, self.geocode_filename
        super(CSVGeocodeData, self).__init__()
  
    def load_countries(self):
        """Load a map of country code to name
        """
        countries = {}
        for code, name in csv.reader(open(self.country_filename)):
            countries[code] = name
        return countries

    def extract(self):
        """Extract geocode data from zip
        """
        coordinates, locations = [], []
        rows = csv.reader(open(self.geocode_filename))
        for latitude, longitude, country_code, city in rows:
            coordinates.append((latitude, longitude))
            locations.append(dict(co=country_code, type=city))

        return coordinates, locations


def test():
    from datetime import datetime
    # test some coordinate lookups
    city1 = (-37.81, 144.96)
    city2 = (31.76, 35.21)
    
    start = datetime.now()
    gd = geo_loader('csv')
    print gd.get(city1)
    print datetime.now() - start
    print

    start = datetime.now()
    gd = geo_loader('csv')
    print gd.search([city1, city2])
    print datetime.now() - start
    print

    start = datetime.now()
    gd = geo_loader('csv')
    print gd.search([(50.839998, 5.693614)])
    print datetime.now() - start
    print
    
    print gd.search([(0, 0)])
    print
    
    print gd.locations[0]
    print gd.coordinates[0]
    print gd.countries[gd.countries.keys()[0]]
    
if __name__ == '__main__':
    test()