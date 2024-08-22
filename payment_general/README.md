# Wire general

## Technical details

This module does not integrate with an API and, instead, uses the payment engine to immediately mark
Wire general transactions as 'pending' to display the 'pending message' containing payment
instructions on the confirmation page.

## Supported features

- Direct payment flow

## Testing instructions

Wire general can be tested indifferently in test or live mode as it does not make API requests.
