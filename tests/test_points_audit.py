import json
import unittest
from unittest import mock

import checkin


class PointsAuditTests(unittest.TestCase):
    def test_read_only_audit_limits_output_to_numeric_ledger_fields(self):
        client = mock.Mock()
        client.req.return_value = {
            'code': 0, 'points': '73', 'email': 'private@example.test',
            'history': [
                {'time': 1794468832000, 'change': '2', 'balance': '73',
                 'user_id': 'private-id', 'detail': 'private-cookie'},
                {'time': 'private-data', 'change': 2},
                {'time': 1794468832000, 'change': 'private-data', 'balance': 'nan'},
            ],
        }
        with mock.patch('checkin.log') as log:
            checkin.audit_points(client)
        client.req.assert_called_once_with('GET', '/api/user/points')
        client.checkin.assert_not_called()
        output = log.call_args.args[0]
        self.assertNotIn('private', output)
        report = json.loads(output.split('POINTS_AUDIT: ', 1)[1])
        self.assertEqual(report['points'], 73)
        self.assertEqual(len(report['history']), 2)
        self.assertEqual(report['history'][0]['change'], 2)
        self.assertIsNone(report['history'][1]['balance'])

    def test_denied_query_does_not_print_response(self):
        client = mock.Mock()
        client.req.return_value = {'code': -2, 'message': 'private-data'}
        with mock.patch('checkin.log') as log:
            checkin.audit_points(client)
        self.assertEqual(log.call_args.args[0], 'POINTS_AUDIT: points query failed')
