from generator import N 

def test():
    timezone = "Europe/Paris"

    link = "https://accounts.hcaptcha.com/demo"

    sitekey = "sitekey"

    jwt = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmIjowLCJzIjoyLCJ0IjoidyIsImQiOiJMbWNDM3Q5R0k3bTk2YXJvYWRJblRDTE40cU9kaFBJcGxKOXl2V2Jtc1pPUXJmWGVVOG9BaVJ0VUNjQVgyaEpBK2w1UHBsaUVqSG1GVEJ4bTQ2UVhHNVlKUTRuczMxcDFLd1ZqMXNUdDJvL3FGd01nRVoyTzB0cnYyTGFJU1Fud1ozKzhQUm1PV2xFT3RCQnFWdmluTnBVVDFzSXh5SmhQK2tkWGRrV2RhaS9SL2FiUThpWlZScHpka3ZzYlIrNmpVT2czSlRadmNzTnc5dVRkdHJIMS9yWnFaZm5rNWhwWjdmWmpSNEMxV2dFREYvT21UbGJjdnVaMm51U0FtMW89R2hmc1V2WWR2Tm4rVkhQUCIsImwiOiIvYy9iNzU4YTliZTAwYTkxMmE5NmQ3ODUwOWYzMjdmNjBjMDA4MzZmMDBkYmE1NWQ4ZTU3MmMzNDhhYzE3ODg5NjQ1IiwiaSI6InNoYTI1Ni1TaVRYSXJKcXBPUWpUd3RSeFNZT0VHZ1FVNzc3Y0JOb1BEVWl5Ui9VOGtRPSIsImUiOjE3NDY3MjczMjYsIm4iOiJoc3ciLCJjIjoxMDAwfQ.1tLK-qpoJW5MbkjtrYhtL_BeU3MJcsSR5hWPt-TArV4"

    a = N(timezone=timezone, link=link, sitekey=sitekey, v2_api=False)

    ndat = a.make_n(jwt=jwt, req_type=None)

    print(ndat)

test()
