import unittest
from theoktany.auth_client import OktaAuthClient, OktaFactors
from theoktany.client import ApiClient
from tests.mb_wrapper import MountebankProcess

user_no_id = dict(id=None, login="terry@aol.com", phone_number="+1-555-555-5555")
user_no_phone_number = dict(id="00000", login="billy@aol.com", phone_number=None)
user_invalid_id = dict(id="invalid_id", login="holly@aol.com", phone_number="+1-555-555-5555")

""" Will receive responses from mountebank """
user_one = dict(id="00001", login="harry@aol.com", phone_number="+1-555-555-5555")
user_two = dict(id="00002", login="bobby@aol.com", phone_number="+1-555-555-5555")
user_three = dict(id="00003", login="freddy@aol.com", phone_number="+1-555-555-5555")


class SMSAuthTests(unittest.TestCase):

    def setUp(self):
        self.api_client = ApiClient(API_TOKEN='jrr-tolkien')
        self.auth_client = OktaAuthClient(OktaFactors(self.api_client))
        self.mb = MountebankProcess()

    def tearDown(self):
        self.mb.destroy_all_imposters()

    def setup_imposter(self, file_name):
        imposter = self.mb.create_imposter('test_auth_client/stubs/' + file_name)
        api_client = ApiClient(BASE_URL=self.mb.get_imposter_url(imposter))
        return OktaAuthClient(OktaFactors(api_client))

    def test_sms_enrollment_requirements(self):
        with self.assertRaises(AssertionError):
            self.auth_client.enroll_user_for_sms(user_no_id.get('id'), user_no_id.get('phone_number'))

        with self.assertRaises(AssertionError):
            self.auth_client.enroll_user_for_sms(
                    user_no_phone_number.get('id'), user_no_phone_number.get('phone_number'))

    def test_sms_enrollment_success(self):
        auth_client = self.setup_imposter('test_sms_enrollment.json')
        response, message, error_code = auth_client.enroll_user_for_sms(
            user_one.get('id'), user_one.get('phone_number'))
        self.assertTrue(response)
        self.assertEqual(response.get('id'), user_one.get('id'))
        self.assertEqual(message, "Success")
        self.assertIsNone(error_code)

    def test_sms_enrollment_failure(self):
        auth_client = self.setup_imposter('test_sms_enrollment.json')
        response, message, error_code = auth_client.enroll_user_for_sms(
            user_two.get('id'), user_two.get('phone_number'))
        self.assertFalse(response)
        self.assertEqual(message, "Factor already exists.")
        self.assertIsNotNone(error_code)

    def test_sms_activation_requirements(self):
        with self.assertRaises(AssertionError):
            self.auth_client.activate_sms_factor(user_no_id.get('id'), '123')

        with self.assertRaises(AssertionError):
            self.auth_client.activate_sms_factor(user_one.get('id'), None)

    def test_sms_activation_success(self):
        auth_client = self.setup_imposter('test_sms_activation.json')
        response, message, error_code = auth_client.activate_sms_factor(user_one.get('id'), '12345')
        self.assertTrue(response)
        self.assertEqual(response.get('id'), user_one.get('id'))
        self.assertEqual(message, "Success")
        self.assertIsNone(error_code)

    def test_sms_activation_failure_one(self):
        auth_client = self.setup_imposter('test_sms_activation.json')
        response, message, error_code = auth_client.activate_sms_factor(user_two.get('id'), 'invalid-passcode')
        self.assertFalse(response)
        self.assertEqual(message, "Your passcode doesn't match our records. Please try again.")
        self.assertEqual('E0000068', error_code)

    def test_sms_activation_failure_two(self):
        auth_client = self.setup_imposter('test_sms_activation.json')
        response, message, error_code = auth_client.activate_sms_factor(user_three.get('id'), '12345')
        self.assertFalse(response)
        self.assertEqual(message, "Not enrolled in factor.")
        self.assertIsNotNone(error_code)

    def test_sms_activation_failure_three(self):
        auth_client = self.setup_imposter('test_sms_activation.json')
        response, message, error_code = auth_client.activate_sms_factor(user_invalid_id.get('id'), '12345')
        self.assertFalse(response)
        self.assertEqual(message, "Not found: Resource not found: invalid_id (User)")
        self.assertIsNotNone(error_code)

    def test_sms_challenge_requirements(self):
        with self.assertRaises(AssertionError):
            self.auth_client.send_sms_challenge(user_no_id.get('id'))

    def test_sms_challenge_success(self):
        auth_client = self.setup_imposter('test_send_sms_challenge.json')
        response, message, error_code = auth_client.send_sms_challenge(user_one.get('id'))
        self.assertTrue(response)
        self.assertEqual(response.get('factorResult'), 'CHALLENGE')
        self.assertEqual(message, "Success")
        self.assertIsNone(error_code)

    def test_sms_challenge_failure_one(self):
        auth_client = self.setup_imposter('test_send_sms_challenge.json')
        response, message, error_code = auth_client.send_sms_challenge(user_two.get('id'))
        self.assertFalse(response)
        self.assertEqual(message, "Your passcode doesn't match our records. Please try again.")
        self.assertEqual('E0000068', error_code)

    def test_sms_challenge_failure_two(self):
        auth_client = self.setup_imposter('test_send_sms_challenge.json')
        response, message, error_code = auth_client.send_sms_challenge(user_invalid_id.get('id'))
        self.assertFalse(response)
        self.assertEqual(message, "Not found: Resource not found: invalid_id (User)")

    def test_sms_challenge_failure_three(self):
        auth_client = self.setup_imposter('test_send_sms_challenge.json')
        response, message, error_code = auth_client.send_sms_challenge(user_three.get('id'))
        self.assertFalse(response)
        self.assertEqual('Not enrolled in factor.', message)
        self.assertIsNotNone(error_code)

    def test_verify_sms_challenge_requirements(self):
        with self.assertRaises(AssertionError):
            self.auth_client.verify_sms_challenge_passcode(user_no_id.get('id'), '12345')

    def test_verify_sms_challenge_success(self):
        auth_client = self.setup_imposter('test_verify_sms_challenge.json')
        response, message, error_code = auth_client.verify_sms_challenge_passcode(user_one.get('id'), '12345')
        self.assertTrue(response)
        self.assertEqual(response.get('factorResult'), 'SUCCESS')
        self.assertEqual(message, "Success")
        self.assertIsNone(error_code)

    def test_verify_sms_challenge_failure_one(self):
        auth_client = self.setup_imposter('test_verify_sms_challenge.json')
        response, message, error_code = auth_client.verify_sms_challenge_passcode(
            user_two.get('id'), "invalid-passcode")
        self.assertFalse(response)
        self.assertEqual(message, "Your passcode doesn't match our records. Please try again.")
        self.assertEqual('E0000068', error_code)

    def test_verify_sms_challenge_failure_two(self):
        auth_client = self.setup_imposter('test_verify_sms_challenge.json')
        response, message, error_code = auth_client.verify_sms_challenge_passcode(user_invalid_id.get('id'), '12345')
        self.assertFalse(response)
        self.assertEqual(message, "Not found: Resource not found: invalid_id (User)")

    def test_verify_sms_challenge_three(self):
        auth_client = self.setup_imposter('test_verify_sms_challenge.json')
        response, message, error_code = auth_client.verify_sms_challenge_passcode(user_three.get('id'), '12345')
        self.assertFalse(response)
        self.assertEqual("Not enrolled in factor.", message)

    def test_user_is_enrolled_in_sms(self):
        auth_client = self.setup_imposter('test_sms_is_enrolled.json')
        is_enrolled = auth_client.is_user_enrolled_for_sms(user_one.get('id'))
        self.assertTrue(is_enrolled)

    def test_user_is_not_enrolled_in_sms_pending_activation(self):
        auth_client = self.setup_imposter('test_sms_is_enrolled.json')
        is_enrolled = auth_client.is_user_enrolled_for_sms(user_two.get('id'))
        self.assertFalse(is_enrolled)

    def test_user_is_not_enrolled_in_sms_different_factor(self):
        auth_client = self.setup_imposter('test_sms_is_enrolled.json')
        is_enrolled = auth_client.is_user_enrolled_for_sms(user_three.get('id'))
        self.assertFalse(is_enrolled)

    def test_user_is_not_enrolled_in_sms_invalid_id(self):
        auth_client = self.setup_imposter('test_sms_is_enrolled.json')
        is_enrolled = auth_client.is_user_enrolled_for_sms("invalid_id")
        self.assertFalse(is_enrolled)

    def test_delete_sms_factor(self):
        auth_client = self.setup_imposter('test_sms_delete_factor.json')
        response, message, error_code = auth_client.delete_sms_factor(user_one['id'])
        self.assertEqual(message, 'Success')
        self.assertIsNone(error_code)

    def test_update_sms_phone_number(self):
        auth_client = self.setup_imposter('test_sms_delete_factor.json')
        new_phone_number = '+1 666-666-6666'
        response, message, error_code = auth_client.update_sms_phone_number(user_one['id'], new_phone_number)
        self.assertTrue(response)
        self.assertEqual(response.get('id'), user_one.get('id'))
        self.assertEqual(response['profile']['phoneNumber'], new_phone_number)
        self.assertEqual(message, "Success")
        self.assertIsNone(error_code)

    def test_update_sms_phone_number_failure(self):
        auth_client = self.setup_imposter('test_sms_delete_factor.json')
        response, message, error_code = auth_client.update_sms_phone_number(user_two['id'], '+1 666-666-6666')
        self.assertFalse(response)
        self.assertEqual('Tom wanted 100% test coverage.', message)
        self.assertIsNotNone(error_code)

    def test_update_sms_phone_number_delete_failure(self):
        auth_client = self.setup_imposter('test_sms_delete_factor.json')
        response, message, error_code = auth_client.update_sms_phone_number(user_three['id'], '+1 666-666-6666')
        self.assertFalse(response)
        self.assertEqual('Tom wanted 100% test coverage.', message)
        self.assertIsNotNone(error_code)
