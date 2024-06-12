import re
import dns.resolver
import smtplib
import pycountry
import concurrent.futures
from colorama import init, Fore

# Initialize colorama
init(autoreset=True)

def is_valid_email(email):
    """ Validate email syntax. """
    email_regex = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    return re.match(email_regex, email) is not None

def get_domain(email):
    """ Extract domain from email address. """
    return email.split('@')[1]

def domain_exists(domain):
    """ Check if domain exists by querying DNS. """
    try:
        dns.resolver.resolve(domain, 'A')
        return True
    except dns.resolver.NXDOMAIN:
        return False

def has_mx_records(domain):
    """ Check if domain has MX records. """
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        return len(mx_records) > 0
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        return False

def smtp_verify(email):
    """ Verify email existence using SMTP. """
    domain = get_domain(email)
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_record = str(mx_records[0].exchange)
        server = smtplib.SMTP(mx_record)
        server.set_debuglevel(0)
        server.helo()
        server.mail('test@example.com')
        code, message = server.rcpt(email)
        server.quit()
        return code == 250
    except:
        return False

def get_country_by_domain(domain):
    """ Infer country from email domain. """
    parts = domain.split('.')
    if len(parts) > 1 and parts[-1].isalpha() and len(parts[-1]) == 2:
        country_code = parts[-1].upper()
        try:
            country = pycountry.countries.get(alpha_2=country_code)
            return country.name if country else "Unknown"
        except KeyError:
            return "Unknown"
    return "Unknown"

def verify_email(email):
    """ Comprehensive email verification. """
    if not is_valid_email(email):
        return (email, False, "Invalid Email Syntax", "Unknown")
    
    domain = get_domain(email)
    
    if not domain_exists(domain):
        return (email, False, "Domain Does Not Exist", "Unknown")
    
    if not has_mx_records(domain):
        return (email, False, "No MX Records", "Unknown")
    
    if not smtp_verify(email):
        return (email, False, "Email Not Verified", get_country_by_domain(domain))
    
    return (email, True, "Verified", get_country_by_domain(domain))

def verify_bulk_emails(emails):
    """ Verify a list of emails in bulk using multi-threading. """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(verify_email, emails))
    return results

def save_valid_emails(results, filename):
    """ Save valid emails to a text file. """
    with open(filename, 'w') as file:
        for email, is_valid, status, country in results:
            if is_valid:
                file.write(f"{email}\n")

def main():
    # Prompt user for the file containing email leads
    input_file = input("Please enter the filename containing the email leads: ")

    try:
        # Read emails from the file
        with open(input_file, 'r') as file:
            emails = [line.strip() for line in file if line.strip()]

        # Verify the emails
        results = verify_bulk_emails(emails)

        # Save valid emails to a file
        save_valid_emails(results, 'valid_emails.txt')

        # Print the results
        for email, is_valid, status, country in results:
            if is_valid:
                print(f"{email} - {Fore.GREEN}{status} - {country}")
            else:
                print(f"{email} - {Fore.RED}{status} - {country}")
    
    except FileNotFoundError:
        print(Fore.RED + "The specified file was not found. Please try again.")

if __name__ == "__main__":
    main()
