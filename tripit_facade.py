from tripit import TripIt, WebAuthCredential


class TripItFacade(object):


    def __init__(self, username, password):
        credential = WebAuthCredential(username, password)
        self._tripit = TripIt(credential)


    def _is_air(self, element):
        return 'display_name' in element.get_attribute_names() and element.get_attribute_value('display_name') == 'Flight'


    def _is_segment(self, element):
        return 'start_airport_code' in element.get_attribute_names() and 'end_airport_code' in element.get_attribute_names()


    def fetch_trips(self, traveler=True, past=True, include_objects=True, page_num=1, page_size=10):
        ret = self._tripit.list_trip({
            'traveler': 'true' if traveler else 'false',
            'past' : 'true' if past else 'false',
            'include_objects' : 'true' if include_objects else 'false',
            'page_num': page_num,
            'page_size': page_size
        })
        return ret


    def list_flight_segments(self):
        ret = []
        page_num = 1
        while True:
            trips = self.fetch_trips(page_num=page_num)
            max_page = int(trips.max_page)
            airs = [i for i in trips.get_children() if self._is_air(i)]

            for i in airs:
                segments = [j for j in i.get_children() if self._is_segment(j)]
                for s in segments:
                    item = {}
                    for attribute in s.get_attribute_names():
                        item[attribute] = s.get_attribute_value(attribute)
                    ret.append(item)
            if page_num < max_page:
                page_num += 1
            else:
                break
        return ret

