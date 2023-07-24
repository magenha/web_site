import pandas as pd
import os
import glob
import matplotlib.pyplot as plt
import numpy as np
import pickle
from datetime import datetime

today = datetime.today().strftime('%B %d., %Y')

def mt_ethnic(x, mt_origins_dict):
    
    group = ""
    for k in mt_origins_dict.keys():
        if x in mt_origins_dict[k]:
            group = str(k)
            break
        else:
            group = "broadly_european"
    
    
    #Check
    if x[0] in ["A", "B", "C", "D", "X"] and group not in list(mt_origins_dict.keys()):
        print(f"Mitochondrial Haplogroup {x} not assigned to asian nor native-americans")
    if x[0] in ["L"] and group not in list(mt_origins_dict.keys()):
        print(f"Mitochondrial Haplogroup {x} not assigned to africans nor guanches")
    
    return group

def y_ethnic(x, y_origins_dict):
    group = ""
    for k in y_origins_dict.keys():
        if x in y_origins_dict[k]:
            group = str(k)
            break
        else:
            group = "broadly_european"
    
    
    #Check
    if x[0] in ["A", "B"] and group not in list(y_origins_dict.keys()):
        print(f"Y Haplogroup {x} not assigned to african")
    if x[0] in ["C", "Q"] and group not in list(y_origins_dict.keys()):
        print(f"Y Haplogroup {x} not assigned to native americans")
    
    return group


def createhtmltable(L):
    
    L_out = []
    for m,i in enumerate(L):
        L_out.append('<tr>')
        L_out.append(f'<th>{m+1}</th>')
        for j in range(4):
            L_out.append(f'<th>{i[j]}</th>')
        L_out.append('</tr>')
    return L_out

                
def create_html_resources_country(country_list):
    text_before = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="with=device-width, initial-scale=1.0">
        <title>RESOURCES</title>
        <link rel="stylesheet" href="../style.css">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Pangolin&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
    </head>
    <body>
    <section class="header">
        <nav>
            <a href="../index.html"><img src="../images/logo.png"></a>
            
            <div class="nav-links" id="navLinks">
                <ul>
                    <li><a href="../index.html">HOME</a></li>
                    <li><a href="">SIGN-IN</a></li>
                    <li><a href="./index-resources.html">RESOURCES</a></li>
                    <li><a href="../Blog/index-blog.html">BLOG</a></li>
                    <li><a href="../Contact/index-contact.html">CONTACT & SUPPORT</a></li>
                </ul>
            </div>
        </nav>
    </section>

    <!--------------------------------CONTENT------------------------------------------->
    <section class="resources-haplogroups-main">

            <h1>Haplogroups of different countries</h1>
            <p>
                With volunteers whose DNA tests have been carried out by 23andme, a small database was built. Most of the donors were cuban-born or of cuban descent, which makes the statistics we have gathered about Cuba the most accurate to date. The data was gathered initially from <em>relatives list</em> of 12 people that kindly donated their .csv files.
                After the social media impact of the MAGENHA page, followers kindly donated their .csv files, from where we extracted new testers which gave us better statistics.
                The following list contains links to the results for various countries. The following are the only ones shown as they are the ones, we have a reasonable amount of info regarding paternal and maternal lineages.
            </p>
            <p>If you have taken a test on 23andme, you can donate your <a href="https://whoareyoumadeof.com/blog/how-to-download-23andme-dna-relatives/">DNA relatives list</a> (<a href="https://www.youtube.com/watch?v=R5rBaJUGyOM&ab_channel=YourDNAGuide">see this video to learn download relatives list</a>). That will help us compute some 
                statistical results, like the ones here presented. 
                There is no personal information in the file, nor from the relatives. Our focus is the grandparent's country of birth and haplogrup of the relatives. Once we extract the information, we delete the file.
                If you are willing to donate your relatives list, please <a href="../Contact/index-contact.html">contact us</a> . Would you like to <a href="../index.html">return home</a>?</p>

    </section>

    <section class="resources-main-panel">\n
    '''

    text_after = '''
    </section>
    <!--------------------------------FOOTER------------------------------------------->


    <section class="footer">
        <div>
            <nav>
                <div class="nav-links" id="nav-links">
                <ul>
                    <li><a href="../terms-conditions.html">TERMS & CONDITIONS</a></li>
                    <li><a href="../faqs.html">FAQs</a></li>
                    <li><a href="../Contact/index-contact.html">DONATE</a></li>
                </ul>
            </div>
            </nav>
        </div>
        <p>MAGENHA 2023 All rights reserved</p>
        <p>Made by Samuel Martinez Alcala</p>
        <div class="social-media-icons">
            <a href="https://www.facebook.com/magenha" target="_blank">
            <i class="fab fa-facebook"></i>
            </a>
            <a href="https://twitter.com/magenhaproject" target="_blank">
            <i class="fab fa-twitter"></i>
            </a>
            <a href="https://www.reddit.com/user/magenha/" target="_blank">
                <i class="fab fa-reddit"></i>
            </a>
            <a href="https://www.linkedin.com/in/magenha-magenha-b5a405271/" target="_blank">
                <i class="fab fa-linkedin"></i>
            </a>
            <a href="https://www.instagram.com/magenhaproject/" target="_blank">
                <i class="fab fa-instagram"></i>
            </a>
            <!-- Add more social media icons and links as needed -->
        </div>
    </section>

    </body>    
    </html>\n
    '''

    global country_dict


    with open(f'./index-resources-haplos-home.html', 'w') as f:
        f.write(text_before)
        for c in countries_list:
            place = country_dict[c]
            f.write('<div class="resources-card">\n')
            f.write(f'<a href="./index-resources-haplos-{c}.html">\n')
            f.write(f'<img src="../images/resources/flags/4x3/{c.lower()}.svg" alt="Card Image">\n')
            f.write(f'<h3>{place}</h3>\n')
            f.write('</a></div>\n')
        f.write(text_after)
    


def create_html_country(country, mt_lin, pat_lin, table):
    global country_dict
    global today
    country_name = country_dict[country]
    
    text = f'''
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="with=device-width, initial-scale=1.0">
    <title>RESOURCES</title>
    <link rel="stylesheet" href="../style.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Pangolin&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
</head>
<body>
<section class="header">
    <nav>
        <a href="../index.html"><img src="../images/logo.png"></a>
        
        <div class="nav-links" id="navLinks">
            <ul>
                <li><a href="../index.html">HOME</a></li>
                <li><a href="">SIGN-IN</a></li>
                <li><a href="./index-resources.html">RESOURCES</a></li>
                <li><a href="../Blog/index-blog.html">BLOG</a></li>
                <li><a href="../Contact/index-contact.html">CONTACT & SUPPORT</a></li>
            </ul>
        </div>
    </nav>
</section>

<!--------------------------------CONTENT------------------------------------------->
    <section class="haplogr-table">

            <h1>Table of most common haplogroups for {country_name}</h1>
            <p>The following is a table of the most common haplogroups obtained for {country_name}.
                If you wish to see other country's information, <a href="./index-resources-haplos-home.html" > GO BACK </a>.
                <br>
                For this country, our database tracks: </p>
                <div class="number-lines"></p>
                <p>Lineages of <span id="bigger-color">mt</span>:<span id="bigger"> {mt_lin} </span></p>
                <p>Lineages of <span id="bigger-color">Y</span>: <span id="bigger"> {pat_lin} </span></p>
                <p>Last update {today}</p>
                </div>
            <table class="center">
                <tr>
                    <th>rank </th>
                    <th> mt haplogroup </th>
                    <th> abundance (%) </th>
                    <th> Y haplogroup </th>
                    <th> abundance (%) </th>
                </tr>\n
    '''
    after_table ='''
    </table>
            

    </section>
    <!--------------------------------FOOTER------------------------------------------->


    <section class="footer">
        <div>
            <nav>
                <div class="nav-links" id="nav-links">
                <ul>
                    <li><a href="../terms-conditions.html">TERMS & CONDITIONS</a></li>
                    <li><a href="../faqs.html">FAQs</a></li>
                    <li><a href="../Contact/index-contact.html">DONATE</a></li>
                </ul>
            </div>
            </nav>
        </div>
        <p>MAGENHA 2023 All rights reserved</p>
        <p>Made by Samuel Martinez Alcala</p>
        <div class="social-media-icons">
            <a href="https://www.facebook.com/magenha" target="_blank">
            <i class="fab fa-facebook"></i>
            </a>
            <a href="https://twitter.com/magenhaproject" target="_blank">
            <i class="fab fa-twitter"></i>
            </a>
            <a href="https://www.reddit.com/user/magenha/" target="_blank">
                <i class="fab fa-reddit"></i>
            </a>
            <a href="https://www.linkedin.com/in/magenha-magenha-b5a405271/" target="_blank">
                <i class="fab fa-linkedin"></i>
            </a>
            <a href="https://www.instagram.com/magenhaproject/" target="_blank">
                <i class="fab fa-instagram"></i>
            </a>
            <!-- Add more social media icons and links as needed -->
        </div>
    </section>

    </body>    
    </html>\n
    '''
    
    with open(f'./index-resources-haplos-{country}.html', 'w') as f:
        f.write(text)
        for element in table:
            f.write(element + '\n')
        f.write(after_table)




#Try to categorize the mt-s and Y-DNAs. 
#  native_americans, guanches, broadly_european, african
mt_origins_dict = {}
mt_origins_dict["africans"] = ["L0", "L0a1b", "L0a1b1a1", "L0a1b2", "L3d1-5", "L3f1b3", "L3d1a", "L1b", "L1c1d", "L02a2",
                               "L1", "L1b1a", "L1b1a2", "L1b1a3", "L1b1a4", "L1b1a5", "L1b1a6","L1c1a2", "L1c3c",
                               "L1b1b" , "L1c1", "L1c1a", "L1c1b", "L1c2", "L1c2a1b", "L1c4", "L1c6", "L1c3a", "L1c3b",
                               "L2", "L2a", "L2a1", "L2a1a", "L2a1a1", "L2a1b", "L2a1c", "L1c5", "L2a1c4", "L2a1c3",
                               "L2a1c1", "L2a2", "L2a1f", "L2b", "L2b1a", "L2c", "L2c2", "L2d", "L3d1b1", "L2e", "L3", "L3a1", 
                               "L3a2", "L3a", "L3b", "L3b1a2", "L3f", "L3f1a", "L3f1b", "L1c2b1", "L3h1b", "L2e2a1b",
                               "L3f1b1", "L3f1b1a", "L3f1b4", "L3f1b4a", "L3f2", "L3f3", "L3c", "L3d", "L3d2", "L3d3a", 
                               "L3d3a1", "L3e", "L3e1", "L3e2a1a", "L3e2a1b", "L3e2b2", "L3e5", "L3f", "L3f1b", "L3i1b", "L3i", 
                               "L3i2", "L3k", "L3x", "L3h", "L3h1", "L3h2", "L3", "L3d1b", "L3e2b", "L3e1e", "L3e2b3", 
                                "L0a2a2", "L2a1a2a1", "L2c3", "L1c", "L1c3b1", "L3e3b", "L2b1a3", "L3e4", "L3e2a", "L3d1a1a", 
                               "L1b1a7", "L1c3b1a", "L2a1d", "L0a1b2a", "L3e1a2", "L2b1a2", "L3d1", "L0a1a", "L1c1_2_4_6", 
                               "L3e2b1a", "L3e1b", "L3e1a1a", "L4b2a", "L3b1", "L1c3b2", "L2b2", "L3d1d", "L2c2a", "L0a2a1", 
                               "L1c2a1", "L1b1a1_4", "L3d1c", "L4b2b", "L4b2", "L3e2a1b1", "L3e1a3", "L2b_c", "L2a1i", "L2a1h", 
                               "L2a1a2", "L1c3", "L1c1b_c_d", "L1c1a1a1a"]
mt_origins_dict["guanches"] = ["J1c3", "H1cf", "H2a", "L3b1a", "T2c1d2", "U6b", "U6b1a", "H1-16260",
                              "U6b1", "U6c"]
mt_origins_dict["native_americans"] = ["A2", "A2c", "A2d", "A2d1", "A2e", "B2","B2b", "B2d", "C1", "C1b", "C1c", "C1d", 
                                       "C1c2", "C4", "C4c", "D1", "D1f1", "D2a", "D4h3a", "X2a", "D1e", "B4a1a1", 
                                       "C1b2a", "C1b4", "B2c", "X6", "X7", "X2a", "X2", "X1b", "X2a1", "X2c", "X2c1"]
mt_origins_dict["asian"] = ["C", "D5a2d1", "X"]
mt_origins_dict["ancient_iberia"] = ["X2b"]
mt_origins_dict["jew_ashkenazi"] = ["L2a1l"]


y_origins_dict={}
y_origins_dict["asian"] = ["O-CTS1875", "C-F1756"]
y_origins_dict["africans"] = ["E-M132", "E-V38", "E-M75", "J-M304", "E-M215", "T-M184"]
y_origins_dict["guanches"] = ["E-M81", "E-M78", "E-M183", "J-M267", "E-M132", "E-M96"]
y_origins_dict["native_americans"] = ["C-M217", "Q-L54", "Q-L205.2", "Q-M3", "Q-M19", "Q-M242", "Q-M346", "Q-MEH2", 
                                      "Q-P89.1", "Q-NWT01", "Q-SA01", "Q-Z780", "R-M173"]



#Locate current directory

path = './Data'
csv_files = glob.glob(os.path.join(path,"matches23andme/*.csv"))

df = pd.DataFrame([])

for f in csv_files:
      
    # read the csv file
    df = pd.concat([df, pd.read_csv(f)])


#Read the db if exists
db_file = './Data/Output/db.pckl'

try:
    db = pd.read_pickle(db_file)
    n_0 = len(db.index)
    df = df.drop_duplicates(subset=['Link to Profile Page'])
    db = pd.concat([db, df], ignore_index=True)
    db = db.drop_duplicates(subset=['Link to Profile Page'])
    n_f = len(db.index)
    print(f'Added {n_f-n_0}')
    db.to_pickle(db_file)
except:
    df = df.drop_duplicates(subset=['Link to Profile Page'])
    df.to_pickle(db_file)
df = db

countries_list = []
sample_pat = pd.DataFrame(df['Paternal Grandfather Birth Country'].value_counts())
sample_mat = pd.DataFrame(df['Maternal Grandmother Birth Country'].value_counts())

sample_pat = sample_pat.merge(sample_mat, left_on=sample_pat.index, right_on=sample_mat.index).head(15)
sample_shutt = sample_pat[sample_pat['Paternal Grandfather Birth Country'] >=100]
sample_shutt = sample_shutt[sample_pat['Maternal Grandmother Birth Country'] >=100] 
countries_list = sample_shutt.key_0.tolist()


country_dict = {'CU': 'Cuba',
                'US': 'United States of America',
                'PR': 'Puerto Rico',
                'MX': 'Mexico',
                'ES': 'Spain',
                'DO': 'Dominican Republic',
                'VE': 'Venezuela',
                'NI': 'Nicaragua',
                'PT': 'Portugal',
                'CO': 'Colombia',
                'SV': 'El Salvador',
                'BR': 'Brazil',
                'HN': 'Honduras',
                'GT': 'Guatemala',
                'GB': 'Great Britain',
                'IT': 'Italy',
                'EC': 'Ecuador',
                'PE': 'Peru',
                'DE': 'Germany',
                'CA': 'Canada',
                'UY': 'Uruguay',
                'RU': 'Russia',
                'CR': 'Costa Rica',
                'PL': 'Poland',
                'CL': 'Chile',
                'PA': 'Panama',
                'AR': 'Argentina',
                'UA': 'Ukraine',
                'IE': 'Ireland',
                'PH': 'Philippines',
                }


create_html_resources_country(countries_list)

for country in countries_list:
    country_name = country_dict[country]

    maternal_lines = df[df['Maternal Grandmother Birth Country'] == country]
    cd = maternal_lines[['Link to Profile Page','Maternal Haplogroup']]
    cd = cd.drop_duplicates()
    cd = cd.dropna()
    a = cd

    paternal_lines = df[df['Paternal Grandfather Birth Country'] == country]
    cdp = paternal_lines[['Link to Profile Page','Paternal Haplogroup']]
    cdp = cdp.drop_duplicates()
    cdp = cdp.dropna()
    b = cdp

    print(f'Lineages of mt for {country}: {len(cd)}')
    print(f'Lineages of Y for {country}: {len(cdp)}')
    n_mt = len(cd)
    n_y = len(cdp)

    dy = b.reset_index()
    dy = dy.merge(dy['Paternal Haplogroup'].apply(lambda s: pd.Series({"y_origin": y_ethnic(s, y_origins_dict)})), 
        left_index=True, right_index=True)
    dyy = dy.groupby("y_origin").count()

    dmt = a.reset_index()
    dmt = dmt.merge(dmt['Maternal Haplogroup'].apply(lambda s: pd.Series({"mt_origin": mt_ethnic(s, mt_origins_dict)})), 
        left_index=True, right_index=True)
    dmtt = dmt.groupby("mt_origin").count()

    print(f'Computing haplogroups for {country}')

    test_y = dy.groupby('Paternal Haplogroup').count()
    test_y = test_y.sort_values(by='index', ascending=False)
    d_y = test_y['index'].to_dict()
    norm_y = len(dy)

    test_mt = dmt.groupby('Maternal Haplogroup').count()
    test_mt = test_mt.sort_values(by='index', ascending=False)
    d_mt = test_mt['index'].to_dict()
    norm_mt = len(dmt)

    import math
    mnh = min(len(d_mt), len(d_y))
    maxmng = max(len(d_mt), len(d_y))
    L = [['' for i in range(4)] for i in range(maxmng)]
    presition = min(1+ int(math.log10(len(dmt))), 1+ int(math.log10(len(dy))))


    for n,k in enumerate(d_y):
        if n<mnh:
            L[n][2] = k
            L[n][3] = round(d_y[k]/norm_y*100,presition)
        else:
            L[n][2] = k
            L[n][3] = round(d_y[k]/norm_y*100,presition)
            L[n][1] = '-'
            L[n][0] = '-'

    for n,k in enumerate(d_mt):
        if n<mnh:
            L[n][0] = k
            L[n][1] = round(d_mt[k]/norm_mt*100,presition)
        else:
            L[n][0] = k
            L[n][1] = round(d_mt[k]/norm_mt*100,presition)
            L[n][2] = '-'
            L[n][3] = '-'

    table_hapl = createhtmltable(L)


            
        

    create_html_country(country, n_mt,n_y, table_hapl)



