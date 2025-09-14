from password_generator import PasswordGenerator

def initialise_strict_password_generator() -> PasswordGenerator:
    """
    Sets up a password generator. See https://pypi.org/project/random-password-generator/
     
    This produces passwords which adhere to Grafana password policy, if enforced.
    See https://grafana.com/docs/grafana/next/setup-grafana/configure-security/configure-authentication/grafana/#strong-password-policy
    """
    strict_pwo = PasswordGenerator()

    # At least 12 characters
    strict_pwo.minlen = 12
    
    # At least one uppercase letter
    strict_pwo.minuchars = 1

    # At least one lowercase letter
    strict_pwo.minlchars = 1

    # At least one number
    strict_pwo.minnumbers = 1

    # At least one special character
    strict_pwo.minschars = 1

    # Don't include a comma in the password generated (else get issues with csv file!)
    strict_pwo.excludeschars = "," 

    return strict_pwo

