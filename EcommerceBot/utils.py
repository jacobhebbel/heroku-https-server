
"""
simulates an actual call to a db; just gives pretend data
"""
def validateUsername(user):
    invalidChars = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')']
    isValid = True
    for char in invalidChars:
        if char in user:
            isValid = False

    return isValid

"""
again would be an actual call to a db; just gives pretend data
"""
def validateTrackingNumber(num):
    invalidSequences = ['432', 'dr3', 'hf2', '111', '625cdw']
    isValid = True
    for sequence in invalidSequences:
        if sequence in num:
            isValid = False
    
    return isValid

"""
more pretend data
"""
def getPackage(user, num):
    packageData = [{'location': 'Dover, USA',
                    'dateOfArrival': '11/10/2025'},
                   {'location': 'Boston, USA',
                    'dateOfArrival': '1/2/3000'}]
    
    userChars = user.split()
    numChars = num.split()
    package = packageData[0]
    
    for char in userChars:
        if char in numChars:
            package = packageData[1]
    return package