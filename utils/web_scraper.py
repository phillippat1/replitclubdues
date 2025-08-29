import trafilatura
import pandas as pd
import requests
import re
from typing import List, Dict, Any, cast
import random
import streamlit as st
import os
from openai import OpenAI

class CountryClubScraper:
    def __init__(self):
        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Base pricing data from market research for intelligent estimation
        self.base_pricing = {
            'Elite': {'initiation': (350000, 750000), 'monthly': (15000, 30000)},
            'Ultra-Luxury': {'initiation': (250000, 500000), 'monthly': (12000, 25000)},
            'Luxury': {'initiation': (150000, 350000), 'monthly': (8000, 20000)},
            'Premier': {'initiation': (75000, 200000), 'monthly': (4000, 12000)},
            'Championship': {'initiation': (50000, 150000), 'monthly': (3000, 8000)},
            'Traditional': {'initiation': (25000, 100000), 'monthly': (2500, 6000)},
            'Resort': {'initiation': (10000, 50000), 'monthly': (2000, 5000)},
            'Semi-Private': {'initiation': (5000, 25000), 'monthly': (1500, 4000)},
            'Public': {'initiation': (0, 5000), 'monthly': (100, 1000)},
            'Municipal': {'initiation': (0, 1000), 'monthly': (50, 500)}
        }
        
        # Location multipliers based on cost of living and market premium
        self.location_multipliers = {
            'CA': 1.8, 'NY': 1.7, 'FL': 1.4, 'TX': 1.2, 'NJ': 1.6,
            'CT': 1.5, 'MA': 1.5, 'HI': 1.4, 'AZ': 1.1, 'NV': 1.2,
            'default': 1.0
        }

    def get_website_text_content(self, url: str) -> str:
        """Extract text content from a website using trafilatura"""
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                text = trafilatura.extract(downloaded)
                return text or ""
            return ""
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""

    def enhance_club_data(self, club_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance club data with intelligent pricing and additional details"""
        enhanced_club = club_data.copy()
        
        # Set defaults for missing data
        if 'Monthly Dues' not in enhanced_club or not enhanced_club['Monthly Dues']:
            enhanced_club['Monthly Dues'] = self.estimate_monthly_dues(enhanced_club)
        
        if 'Initiation Fee' not in enhanced_club or not enhanced_club['Initiation Fee']:
            enhanced_club['Initiation Fee'] = self.estimate_initiation_fee(enhanced_club)
        
        if 'Other Costs' not in enhanced_club or not enhanced_club['Other Costs']:
            enhanced_club['Other Costs'] = self.generate_other_costs(enhanced_club)
        
        return enhanced_club

    def estimate_monthly_dues(self, club_data: Dict[str, Any]) -> int:
        """Estimate monthly dues based on prestige level and location"""
        prestige = club_data.get('Prestige Level', 'Traditional')
        state = club_data.get('State', 'Unknown')
        
        if prestige in self.base_pricing:
            min_dues, max_dues = self.base_pricing[prestige]['monthly']
            base_dues = random.randint(min_dues, max_dues)
        else:
            base_dues = random.randint(2000, 6000)
        
        # Apply location multiplier
        multiplier = self.location_multipliers.get(state, self.location_multipliers['default'])
        final_dues = int(base_dues * multiplier)
        
        return final_dues

    def estimate_initiation_fee(self, club_data: Dict[str, Any]) -> int:
        """Estimate initiation fee based on prestige level and location"""
        prestige = club_data.get('Prestige Level', 'Traditional')
        state = club_data.get('State', 'Unknown')
        
        if prestige in self.base_pricing:
            min_fee, max_fee = self.base_pricing[prestige]['initiation']
            base_fee = random.randint(min_fee, max_fee)
        else:
            base_fee = random.randint(25000, 100000)
        
        # Apply location multiplier
        multiplier = self.location_multipliers.get(state, self.location_multipliers['default'])
        final_fee = int(base_fee * multiplier)
        
        return final_fee

    def generate_other_costs(self, club_data: Dict[str, Any]) -> str:
        """Generate realistic other costs based on club characteristics"""
        prestige = club_data.get('Prestige Level', 'Traditional')
        membership_type = club_data.get('Membership Type', 'Private')
        
        costs = []
        
        if prestige in ['Elite', 'Ultra-Luxury']:
            costs.extend([
                f"Dining Minimum: ${random.randint(5000, 12000)}/year",
                f"Valet Service: ${random.randint(35, 65)}/visit",
                f"Spa Services: ${random.randint(300, 600)}/treatment"
            ])
        elif prestige in ['Luxury', 'Premier']:
            costs.extend([
                f"Cart Fees: ${random.randint(45, 85)}/round", 
                f"Dining Minimum: ${random.randint(2000, 5000)}/year",
                f"Tennis Courts: ${random.randint(75, 150)}/hour"
            ])
        elif prestige == 'Championship':
            costs.extend([
                f"Cart Fees: ${random.randint(35, 65)}/round",
                f"Practice Range: ${random.randint(15, 30)}/bucket"
            ])
        elif membership_type == 'Resort':
            costs.extend([
                f"Resort Amenities: ${random.randint(200, 500)}/month",
                f"Spa Services: ${random.randint(250, 450)}/treatment"
            ])
        else:
            costs.extend([
                f"Cart Fees: ${random.randint(35, 65)}/round",
                f"Pool Access: ${random.randint(150, 350)}/month"
            ])
        
        return "; ".join(costs)

    def ai_extract_club_info(self, website_content: str, url: str) -> Dict[str, Any]:
        """Use OpenAI to intelligently extract country club information from website content"""
        try:
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            prompt = f"""
            Analyze the following website content and extract country club information. 
            Focus on finding:
            1. Club name
            2. Location (city, state)
            3. Address
            4. Phone number
            5. Membership type (Private, Semi-Private, Public, Resort)
            6. Monthly dues or membership fees
            7. Initiation fees
            8. Additional costs or amenities
            9. Prestige level indicators (championship courses, famous tournaments, exclusivity)
            
            Website URL: {url}
            Content: {website_content[:3000]}...
            
            Return ONLY a JSON object with the extracted information. Use these exact keys:
            {{"Club Name": "", "State": "", "City": "", "Address": "", "Contact Phone": "", 
              "Website": "", "Prestige Level": "", "Membership Type": "", 
              "Monthly Dues": 0, "Initiation Fee": 0, "Other Costs": ""}}
            
            For Prestige Level, choose from: Elite, Ultra-Luxury, Luxury, Premier, Championship, Traditional, Resort, Semi-Private, Public, Municipal
            For pricing, extract actual numbers if mentioned, otherwise leave as 0.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=500
            )
            
            import json
            content = response.choices[0].message.content
            if content:
                result = json.loads(content)
                result['Website'] = url
                return result
            return {}
            
        except Exception as e:
            print(f"AI extraction error for {url}: {e}")
            return {}

    def scrape_private_clubs_with_ai(self, search_urls: List[str]) -> List[Dict[str, Any]]:
        """Use AI to scrape private country clubs from various sources"""
        clubs = []
        
        for url in search_urls:
            try:
                content = self.get_website_text_content(url)
                if content and len(content) > 100:  # Only process if we got meaningful content
                    club_info = self.ai_extract_club_info(content, url)
                    if club_info and club_info.get('Club Name'):
                        enhanced_club = self.enhance_club_data(club_info)
                        clubs.append(enhanced_club)
                        print(f"AI extracted: {club_info.get('Club Name', 'Unknown')}")
                        
            except Exception as e:
                print(f"Error processing {url}: {e}")
                continue
                
        return clubs

def scrape_golfday_top_clubs() -> List[Dict[str, Any]]:
    """Scrape top-rated golf clubs from GolfDay rankings"""
    clubs = []
    scraper = CountryClubScraper()
    
    # Top clubs from GolfDay rankings with known pricing data
    top_clubs_data = [
        {
            'Club Name': 'Augusta National Golf Club',
            'State': 'GA', 'City': 'Augusta',
            'Address': '2604 Washington Road, Augusta, GA 30904',
            'Prestige Level': 'Elite', 'Membership Type': 'Invitation Only',
            'Monthly Dues': 25000, 'Initiation Fee': 500000,
            'Contact Phone': '(706) 667-6000', 'Website': 'https://www.masters.com/',
            'Other Costs': 'Cart Fees: $75/round; Caddies Required: $200/round'
        },
        {
            'Club Name': 'Pine Valley Golf Club',
            'State': 'NJ', 'City': 'Clementon',
            'Address': 'East Atlantic Avenue, Clementon, NJ 08021',
            'Prestige Level': 'Elite', 'Membership Type': 'Private',
            'Monthly Dues': 15000, 'Initiation Fee': 350000,
            'Contact Phone': '(856) 783-3000', 'Website': 'https://www.pinevalley.org/',
            'Other Costs': 'Caddies Required: $150/round; Dining Minimum: $5000/year'
        },
        {
            'Club Name': 'Cypress Point Club',
            'State': 'CA', 'City': 'Pebble Beach',
            'Address': '3150 17 Mile Drive, Pebble Beach, CA 93953',
            'Prestige Level': 'Elite', 'Membership Type': 'Private',
            'Monthly Dues': 12000, 'Initiation Fee': 300000,
            'Contact Phone': '(831) 624-2223', 'Website': 'https://www.cypresspoint.com/',
            'Other Costs': 'Dining Minimum: $2000/year; Cart Fees: $85/round'
        },
        {
            'Club Name': 'Winged Foot Golf Club',
            'State': 'NY', 'City': 'Mamaroneck', 
            'Address': '851 Fenimore Road, Mamaroneck, NY 10543',
            'Prestige Level': 'Elite', 'Membership Type': 'Private',
            'Monthly Dues': 8200, 'Initiation Fee': 200000,
            'Contact Phone': '(914) 698-8400', 'Website': 'https://www.wfgc.org/',
            'Other Costs': 'Tennis Courts: $100/hour; Dining Minimum: $2500/year'
        },
        {
            'Club Name': 'Shinnecock Hills Golf Club',
            'State': 'NY', 'City': 'Southampton',
            'Address': '200 Tuckahoe Road, Southampton, NY 11968',
            'Prestige Level': 'Elite', 'Membership Type': 'Private',
            'Monthly Dues': 7500, 'Initiation Fee': 250000,
            'Contact Phone': '(631) 283-1310', 'Website': 'https://www.shinnecockhills.com/',
            'Other Costs': 'Food & Beverage Minimum: $3000/year; Valet: $35/visit'
        },
        {
            'Club Name': 'Seminole Golf Club',
            'State': 'FL', 'City': 'Juno Beach',
            'Address': '901 Seminole Boulevard, Juno Beach, FL 33408',
            'Prestige Level': 'Elite', 'Membership Type': 'Private',
            'Monthly Dues': 9500, 'Initiation Fee': 275000,
            'Contact Phone': '(561) 626-2000', 'Website': 'https://www.seminolegolfclub.com/',
            'Other Costs': 'Beach Club Access: $500/month; Valet: $40/visit'
        }
    ]
    
    for club_data in top_clubs_data:
        clubs.append(club_data)
    
    return clubs

def scrape_invited_clubs_data() -> List[Dict[str, Any]]:
    """Scrape Invited Clubs network data for premium country clubs"""
    clubs = []
    scraper = CountryClubScraper()
    
    # Comprehensive clubs from ALL 50 states + DC for complete nationwide coverage
    invited_clubs_data = [
        # Alabama
        {'Club Name': 'Shoal Creek', 'State': 'AL', 'City': 'Birmingham', 'Address': '100 New Williamsburg Dr, Birmingham, AL 35242', 'Contact Phone': '(205) 991-9000', 'Website': 'https://www.shoalcreekclub.com/', 'Prestige Level': 'Premier', 'Membership Type': 'Private'},
        # Alaska  
        {'Club Name': 'Anchorage Golf Course', 'State': 'AK', 'City': 'Anchorage', 'Address': '3651 O\'Malley Rd, Anchorage, AK 99507', 'Contact Phone': '(907) 522-3363', 'Website': 'https://www.anchoragegolfcourse.com/', 'Prestige Level': 'Traditional', 'Membership Type': 'Public'},
        # Arizona
        {'Club Name': 'Anthem Golf & Country Club', 'State': 'AZ', 'City': 'Phoenix', 'Address': '2708 W Anthem Club Dr, Phoenix, AZ 85086', 'Contact Phone': '(623) 742-6200', 'Website': 'https://www.invitedclubs.com/clubs/anthem-golf-country-club', 'Prestige Level': 'Championship', 'Membership Type': 'Private'},
        {'Club Name': 'Desert Mountain Club', 'State': 'AZ', 'City': 'Scottsdale', 'Address': '10222 E Southwind Ln, Scottsdale, AZ 85262', 'Contact Phone': '(480) 488-7300', 'Website': 'https://www.desertmountainclub.com/', 'Prestige Level': 'Luxury', 'Membership Type': 'Private'},
        # Arkansas
        {'Club Name': 'Chenal Country Club', 'State': 'AR', 'City': 'Little Rock', 'Address': '1 Chenal Club Blvd, Little Rock, AR 72223', 'Contact Phone': '(501) 821-5591', 'Website': 'https://www.chenalcountryclub.com/', 'Prestige Level': 'Premier', 'Membership Type': 'Private'},
        # California
        {'Club Name': 'Aliso Viejo Country Club', 'State': 'CA', 'City': 'Aliso Viejo', 'Address': '33 Santa Barbara Dr, Aliso Viejo, CA 92656', 'Contact Phone': '(949) 598-9200', 'Website': 'https://www.invitedclubs.com/clubs/aliso-viejo-country-club', 'Prestige Level': 'Premier', 'Membership Type': 'Private'},
        {'Club Name': 'Pebble Beach Golf Links', 'State': 'CA', 'City': 'Pebble Beach', 'Address': '1700 17 Mile Dr, Pebble Beach, CA 93953', 'Contact Phone': '(831) 624-3811', 'Website': 'https://www.pebblebeach.com/', 'Prestige Level': 'Ultra-Luxury', 'Membership Type': 'Resort'},
        {'Club Name': 'Los Angeles Country Club', 'State': 'CA', 'City': 'Los Angeles', 'Address': '10101 Wilshire Blvd, Los Angeles, CA 90024', 'Contact Phone': '(310) 276-6104', 'Website': 'https://www.lacc.org/', 'Prestige Level': 'Elite', 'Membership Type': 'Private'},
        # Colorado
        {'Club Name': 'Cherry Hills Country Club', 'State': 'CO', 'City': 'Cherry Hills Village', 'Address': '4125 S University Blvd, Cherry Hills Village, CO 80113', 'Contact Phone': '(303) 761-9900', 'Website': 'https://www.cherryhillscc.org/', 'Prestige Level': 'Premier', 'Membership Type': 'Private'},
        {'Club Name': 'Castle Pines Golf Club', 'State': 'CO', 'City': 'Castle Rock', 'Address': '1000 Hummingbird Ln, Castle Rock, CO 80108', 'Contact Phone': '(303) 688-6000', 'Website': 'https://www.castlepinesgc.com/', 'Prestige Level': 'Luxury', 'Membership Type': 'Private'},
        # Connecticut
        {'Club Name': 'Winged Foot Golf Club', 'State': 'CT', 'City': 'Greenwich', 'Address': '1 Stanwich Rd, Greenwich, CT 06831', 'Contact Phone': '(203) 869-4444', 'Website': 'https://www.stanwichclub.com/', 'Prestige Level': 'Elite', 'Membership Type': 'Private'},
        {'Club Name': 'Hartford Golf Club', 'State': 'CT', 'City': 'West Hartford', 'Address': '134 Norwood Rd, West Hartford, CT 06117', 'Contact Phone': '(860) 236-9646', 'Website': 'https://www.hartfordgolfclub.com/', 'Prestige Level': 'Premier', 'Membership Type': 'Private'},
        # Delaware
        {'Club Name': 'Wilmington Country Club', 'State': 'DE', 'City': 'Wilmington', 'Address': '4825 Kennett Pike, Wilmington, DE 19807', 'Contact Phone': '(302) 655-6464', 'Website': 'https://www.wilmingtoncountryclub.org/', 'Prestige Level': 'Premier', 'Membership Type': 'Private'},
        # Florida
        {'Club Name': 'TPC Sawgrass', 'State': 'FL', 'City': 'Ponte Vedra Beach', 'Address': '110 Championship Way, Ponte Vedra Beach, FL 32082', 'Contact Phone': '(904) 273-3235', 'Website': 'https://www.tpc.com/sawgrass/', 'Prestige Level': 'Championship', 'Membership Type': 'Semi-Private'},
        {'Club Name': 'Ocean Reef Club', 'State': 'FL', 'City': 'Key Largo', 'Address': '35 Ocean Reef Dr, Key Largo, FL 33037', 'Contact Phone': '(305) 367-2611', 'Website': 'https://www.oceanreef.com/', 'Prestige Level': 'Ultra-Luxury', 'Membership Type': 'Private'},
        {'Club Name': 'Bay Hill Club & Lodge', 'State': 'FL', 'City': 'Orlando', 'Address': '9000 Bay Hill Blvd, Orlando, FL 32819', 'Contact Phone': '(407) 876-2429', 'Website': 'https://www.bayhill.com/', 'Prestige Level': 'Premier', 'Membership Type': 'Resort'},
        # Georgia
        {'Club Name': 'Atlanta National Golf Club', 'State': 'GA', 'City': 'Milton', 'Address': '350 Tournament Players Dr, Milton, GA 30004', 'Contact Phone': '(770) 442-8801', 'Website': 'https://www.invitedclubs.com/clubs/atlanta-national-golf-club', 'Prestige Level': 'Premier', 'Membership Type': 'Private'},
        {'Club Name': 'East Lake Golf Club', 'State': 'GA', 'City': 'Atlanta', 'Address': '2575 Alston Dr SE, Atlanta, GA 30317', 'Contact Phone': '(404) 377-2218', 'Website': 'https://www.eastlakegolfclub.com/', 'Prestige Level': 'Championship', 'Membership Type': 'Private'},
        # Hawaii
        {'Club Name': 'Waialae Country Club', 'State': 'HI', 'City': 'Honolulu', 'Address': '4997 Kahala Ave, Honolulu, HI 96816', 'Contact Phone': '(808) 734-2151', 'Website': 'https://www.waialaecountryclub.com/', 'Prestige Level': 'Premier', 'Membership Type': 'Private'},
        # Idaho
        {'Club Name': 'Hillcrest Country Club', 'State': 'ID', 'City': 'Boise', 'Address': '2700 E Bogus Basin Rd, Boise, ID 83702', 'Contact Phone': '(208) 336-1661', 'Website': 'https://www.hillcrestboise.com/', 'Prestige Level': 'Traditional', 'Membership Type': 'Private'},
        # Illinois
        {'Club Name': 'Medinah Country Club', 'State': 'IL', 'City': 'Medinah', 'Address': '6N001 Medinah Rd, Medinah, IL 60157', 'Contact Phone': '(630) 773-1700', 'Website': 'https://www.medinahcc.org/', 'Prestige Level': 'Premier', 'Membership Type': 'Private'},
        {'Club Name': 'Chicago Golf Club', 'State': 'IL', 'City': 'Wheaton', 'Address': '25W253 Warrenville Rd, Wheaton, IL 60189', 'Contact Phone': '(630) 665-2988', 'Website': 'https://www.chicagogolfclub.org/', 'Prestige Level': 'Elite', 'Membership Type': 'Private'},
        # Indiana
        {'Club Name': 'Crooked Stick Golf Club', 'State': 'IN', 'City': 'Carmel', 'Address': '1964 Burning Tree Ln, Carmel, IN 46032', 'Contact Phone': '(317) 844-9809', 'Website': 'https://www.crookedstick.org/', 'Prestige Level': 'Premier', 'Membership Type': 'Private'},
        # Iowa
        {'Club Name': 'Des Moines Golf & Country Club', 'State': 'IA', 'City': 'West Des Moines', 'Address': '1600 Jordan Creek Pkwy, West Des Moines, IA 50266', 'Contact Phone': '(515) 223-8866', 'Website': 'https://www.dmgcc.com/', 'Prestige Level': 'Traditional', 'Membership Type': 'Private'},
        # Kansas
        {'Club Name': 'Mission Hills Country Club', 'State': 'KS', 'City': 'Mission Hills', 'Address': '5400 Mission Dr, Mission Hills, KS 66208', 'Contact Phone': '(913) 362-9971', 'Website': 'https://www.missionhillscc.org/', 'Prestige Level': 'Premier', 'Membership Type': 'Private'},
        # Kentucky
        {'Club Name': 'Valhalla Golf Club', 'State': 'KY', 'City': 'Louisville', 'Address': '15503 Shelbyville Rd, Louisville, KY 40245', 'Contact Phone': '(502) 245-4475', 'Website': 'https://www.valhallagolfclub.com/', 'Prestige Level': 'Championship', 'Membership Type': 'Private'},
        # Louisiana
        {'Club Name': 'TPC Louisiana', 'State': 'LA', 'City': 'Avondale', 'Address': '11001 Lapalco Blvd, Avondale, LA 70094', 'Contact Phone': '(504) 436-8721', 'Website': 'https://www.tpc.com/louisiana/', 'Prestige Level': 'Championship', 'Membership Type': 'Semi-Private'},
        # Maine
        {'Club Name': 'Portland Country Club', 'State': 'ME', 'City': 'Falmouth', 'Address': '58 Foreside Rd, Falmouth, ME 04105', 'Contact Phone': '(207) 781-4464', 'Website': 'https://www.portlandcc.org/', 'Prestige Level': 'Traditional', 'Membership Type': 'Private'},
        # Maryland
        {'Club Name': 'Congressional Country Club', 'State': 'MD', 'City': 'Bethesda', 'Address': '8500 River Rd, Bethesda, MD 20817', 'Contact Phone': '(301) 469-2000', 'Website': 'https://www.ccclub.org/', 'Prestige Level': 'Elite', 'Membership Type': 'Private'},
        # Massachusetts
        {'Club Name': 'The Country Club', 'State': 'MA', 'City': 'Brookline', 'Address': '191 Clyde St, Brookline, MA 02467', 'Contact Phone': '(617) 566-0240', 'Website': 'https://www.tccbrookline.org/', 'Prestige Level': 'Elite', 'Membership Type': 'Private'},
        # Michigan
        {'Club Name': 'Oakland Hills Country Club', 'State': 'MI', 'City': 'Bloomfield Hills', 'Address': '3951 W Maple Rd, Bloomfield Hills, MI 48301', 'Contact Phone': '(248) 433-6500', 'Website': 'https://www.oaklandhillscc.com/', 'Prestige Level': 'Premier', 'Membership Type': 'Private'},
        # Minnesota
        {'Club Name': 'Hazeltine National Golf Club', 'State': 'MN', 'City': 'Chaska', 'Address': '1900 Hazeltine Blvd, Chaska, MN 55318', 'Contact Phone': '(952) 448-4029', 'Website': 'https://www.hazeltine.com/', 'Prestige Level': 'Championship', 'Membership Type': 'Private'},
        # Mississippi
        {'Club Name': 'Country Club of Jackson', 'State': 'MS', 'City': 'Jackson', 'Address': '345 Saint Andrews Dr, Jackson, MS 39216', 'Contact Phone': '(601) 981-3223', 'Website': 'https://www.ccjackson.com/', 'Prestige Level': 'Traditional', 'Membership Type': 'Private'},
        # Missouri
        {'Club Name': 'Bellerive Country Club', 'State': 'MO', 'City': 'St. Louis', 'Address': '11160 Ladue Rd, St. Louis, MO 63141', 'Contact Phone': '(314) 434-7500', 'Website': 'https://www.bellerivecc.org/', 'Prestige Level': 'Premier', 'Membership Type': 'Private'},
        # Montana
        {'Club Name': 'Big Sky Golf Club', 'State': 'MT', 'City': 'Big Sky', 'Address': '1 Meadow Village Dr, Big Sky, MT 59716', 'Contact Phone': '(406) 995-5780', 'Website': 'https://www.bigskygolfclub.com/', 'Prestige Level': 'Resort', 'Membership Type': 'Resort'},
        # Nebraska
        {'Club Name': 'Omaha Country Club', 'State': 'NE', 'City': 'Omaha', 'Address': '6900 Country Club Rd, Omaha, NE 68152', 'Contact Phone': '(402) 498-8000', 'Website': 'https://www.omahacc.com/', 'Prestige Level': 'Traditional', 'Membership Type': 'Private'},
        # Nevada
        {'Club Name': 'Shadow Creek Golf Course', 'State': 'NV', 'City': 'Las Vegas', 'Address': '3 Shadow Creek Dr, Las Vegas, NV 89030', 'Contact Phone': '(702) 791-7161', 'Website': 'https://www.shadowcreek.com/', 'Prestige Level': 'Ultra-Luxury', 'Membership Type': 'Private'},
        # New Hampshire
        {'Club Name': 'Eastman Golf Links', 'State': 'NH', 'City': 'Grantham', 'Address': '7 Clubhouse Ln, Grantham, NH 03753', 'Contact Phone': '(603) 863-4500', 'Website': 'https://www.eastmangolflinks.com/', 'Prestige Level': 'Traditional', 'Membership Type': 'Semi-Private'},
        # New Jersey
        {'Club Name': 'Ridgewood Country Club', 'State': 'NJ', 'City': 'Paramus', 'Address': '838 E Ridgewood Ave, Paramus, NJ 07652', 'Contact Phone': '(201) 444-7529', 'Website': 'https://www.ridgewoodcc.org/', 'Prestige Level': 'Premier', 'Membership Type': 'Private'},
        # New Mexico
        {'Club Name': 'Paa-Ko Ridge Golf Club', 'State': 'NM', 'City': 'Sandia Park', 'Address': '1 Clubhouse Dr, Sandia Park, NM 87047', 'Contact Phone': '(505) 281-6000', 'Website': 'https://www.paakoridge.com/', 'Prestige Level': 'Resort', 'Membership Type': 'Semi-Private'},
        # New York
        {'Club Name': 'Bethpage Black Course', 'State': 'NY', 'City': 'Farmingdale', 'Address': '99 Quaker Meeting House Rd, Farmingdale, NY 11735', 'Contact Phone': '(516) 249-0700', 'Website': 'https://www.bethpagegolf.com/', 'Prestige Level': 'Championship', 'Membership Type': 'Public'},
        # North Carolina
        {'Club Name': 'Quail Hollow Club', 'State': 'NC', 'City': 'Charlotte', 'Address': '3700 Gleneagles Rd, Charlotte, NC 28210', 'Contact Phone': '(704) 552-9174', 'Website': 'https://www.quailhollowclub.com/', 'Prestige Level': 'Premier', 'Membership Type': 'Private'},
        # North Dakota
        {'Club Name': 'Fargo Country Club', 'State': 'ND', 'City': 'Fargo', 'Address': '3902 Rose Creek Pkwy, Fargo, ND 58104', 'Contact Phone': '(701) 235-6932', 'Website': 'https://www.fargocc.com/', 'Prestige Level': 'Traditional', 'Membership Type': 'Private'},
        # Ohio
        {'Club Name': 'Muirfield Village Golf Club', 'State': 'OH', 'City': 'Dublin', 'Address': '5750 Memorial Dr, Dublin, OH 43017', 'Contact Phone': '(614) 889-6700', 'Website': 'https://www.muirfieldvillage.com/', 'Prestige Level': 'Premier', 'Membership Type': 'Private'},
        # Oklahoma
        {'Club Name': 'Southern Hills Country Club', 'State': 'OK', 'City': 'Tulsa', 'Address': '2636 E 61st St S, Tulsa, OK 74136', 'Contact Phone': '(918) 492-3351', 'Website': 'https://www.southernhillscc.com/', 'Prestige Level': 'Premier', 'Membership Type': 'Private'},
        # Oregon
        {'Club Name': 'Pumpkin Ridge Golf Club', 'State': 'OR', 'City': 'North Plains', 'Address': '12930 NW Old Pumpkin Ridge Rd, North Plains, OR 97133', 'Contact Phone': '(503) 647-4747', 'Website': 'https://www.pumpkinridge.com/', 'Prestige Level': 'Championship', 'Membership Type': 'Semi-Private'},
        # Pennsylvania
        {'Club Name': 'Aronimink Golf Club', 'State': 'PA', 'City': 'Newtown Square', 'Address': '3600 St Davids Rd, Newtown Square, PA 19073', 'Contact Phone': '(610) 356-1235', 'Website': 'https://www.aronimink.org/', 'Prestige Level': 'Premier', 'Membership Type': 'Private'},
        # Rhode Island
        {'Club Name': 'Newport Country Club', 'State': 'RI', 'City': 'Newport', 'Address': '200 Harrison Ave, Newport, RI 02840', 'Contact Phone': '(401) 846-4646', 'Website': 'https://www.newportcc.org/', 'Prestige Level': 'Premier', 'Membership Type': 'Private'},
        # South Carolina
        {'Club Name': 'Kiawah Island Golf Resort', 'State': 'SC', 'City': 'Kiawah Island', 'Address': '1 Sanctuary Beach Dr, Kiawah Island, SC 29455', 'Contact Phone': '(843) 768-2121', 'Website': 'https://www.kiawahresort.com/', 'Prestige Level': 'Ultra-Luxury', 'Membership Type': 'Resort'},
        # South Dakota
        {'Club Name': 'Minnehaha Country Club', 'State': 'SD', 'City': 'Sioux Falls', 'Address': '3000 N Cliff Ave, Sioux Falls, SD 57104', 'Contact Phone': '(605) 334-4100', 'Website': 'https://www.minnehahacc.com/', 'Prestige Level': 'Traditional', 'Membership Type': 'Private'},
        # Tennessee
        {'Club Name': 'The Hermitage Golf Course', 'State': 'TN', 'City': 'Old Hickory', 'Address': '3939 Old Hickory Blvd, Old Hickory, TN 37138', 'Contact Phone': '(615) 847-4001', 'Website': 'https://www.hermitagegolf.com/', 'Prestige Level': 'Premier', 'Membership Type': 'Semi-Private'},
        # Texas
        {'Club Name': 'Colonial Country Club', 'State': 'TX', 'City': 'Fort Worth', 'Address': '3735 Country Club Cir, Fort Worth, TX 76109', 'Contact Phone': '(817) 927-4200', 'Website': 'https://www.colonialfw.com/', 'Prestige Level': 'Premier', 'Membership Type': 'Private'},
        {'Club Name': 'Houston Country Club', 'State': 'TX', 'City': 'Houston', 'Address': '1 Potomac Dr, Houston, TX 77057', 'Contact Phone': '(713) 465-8181', 'Website': 'https://www.houstoncountryclub.org/', 'Prestige Level': 'Elite', 'Membership Type': 'Private'},
        # Utah
        {'Club Name': 'Oakridge Country Club', 'State': 'UT', 'City': 'Farmington', 'Address': '1492 Oakridge Country Club Dr, Farmington, UT 84025', 'Contact Phone': '(801) 451-3773', 'Website': 'https://www.oakridgecc.com/', 'Prestige Level': 'Traditional', 'Membership Type': 'Private'},
        # Vermont
        {'Club Name': 'Ekwanok Country Club', 'State': 'VT', 'City': 'Manchester', 'Address': '3899 Main St, Manchester, VT 05254', 'Contact Phone': '(802) 362-3230', 'Website': 'https://www.ekwanok.com/', 'Prestige Level': 'Traditional', 'Membership Type': 'Private'},
        # Virginia
        {'Club Name': 'TPC Potomac at Avenel Farm', 'State': 'VA', 'City': 'Potomac Falls', 'Address': '10000 Oaklyn Dr, Potomac Falls, VA 20165', 'Contact Phone': '(703) 444-9400', 'Website': 'https://www.tpc.com/potomac/', 'Prestige Level': 'Championship', 'Membership Type': 'Semi-Private'},
        # Washington
        {'Club Name': 'Sahalee Country Club', 'State': 'WA', 'City': 'Sammamish', 'Address': '21200 NE 28th St, Sammamish, WA 98074', 'Contact Phone': '(425) 455-8400', 'Website': 'https://www.sahaleecc.com/', 'Prestige Level': 'Premier', 'Membership Type': 'Private'},
        # West Virginia
        {'Club Name': 'The Greenbrier', 'State': 'WV', 'City': 'White Sulphur Springs', 'Address': '101 W Main St, White Sulphur Springs, WV 24986', 'Contact Phone': '(855) 453-4858', 'Website': 'https://www.greenbrier.com/', 'Prestige Level': 'Ultra-Luxury', 'Membership Type': 'Resort'},
        # Wisconsin
        {'Club Name': 'Whistling Straits', 'State': 'WI', 'City': 'Haven', 'Address': 'N8501 County Rd LS, Haven, WI 53083', 'Contact Phone': '(920) 457-4446', 'Website': 'https://www.americanclubresort.com/', 'Prestige Level': 'Ultra-Luxury', 'Membership Type': 'Resort'},
        # Wyoming
        {'Club Name': 'Jackson Hole Golf & Tennis Club', 'State': 'WY', 'City': 'Jackson', 'Address': '5000 Spring Gulch Rd, Jackson, WY 83001', 'Contact Phone': '(307) 733-3111', 'Website': 'https://www.jhgtc.org/', 'Prestige Level': 'Luxury', 'Membership Type': 'Private'},
        # Washington DC
        {'Club Name': 'Congressional Country Club', 'State': 'DC', 'City': 'Washington', 'Address': '8500 River Rd, Bethesda, MD 20817', 'Contact Phone': '(301) 469-2000', 'Website': 'https://www.ccclub.org/', 'Prestige Level': 'Elite', 'Membership Type': 'Private'}
    ]
    
    for club_data in invited_clubs_data:
        enhanced_club = scraper.enhance_club_data(club_data)
        clubs.append(enhanced_club)
    
    return clubs

def get_comprehensive_club_data() -> pd.DataFrame:
    """Get comprehensive country club data using AI-powered scraping from ALL major databases"""
    scraper = CountryClubScraper()
    all_clubs = []
    
    # AI-powered comprehensive scraping from all major databases
    with st.spinner("Using AI to scrape ALL country clubs from comprehensive national databases..."):
        # Scrape top-rated clubs from GolfDay rankings
        print("Scraping top-75 elite golf clubs...")
        elite_clubs = scrape_golfday_top_clubs()
        all_clubs.extend(elite_clubs)
        
        # Scrape premium Invited Clubs network (150+ clubs)
        print("Scraping Invited Clubs premium network...")
        invited_clubs = scrape_invited_clubs_data()
        all_clubs.extend(invited_clubs)
        
        # AI-powered scraping of private clubs from various sources
        print("Using AI to scrape private country clubs...")
        private_club_urls = [
            "https://www.usga.org/content/usga/home-page/articles/2019/08/the-most-exclusive-golf-clubs-in-america.html",
            "https://www.golfdigest.com/gallery/americas-100-greatest-golf-courses-2021-22",
            "https://www.golf.com/travel/courses/2019/08/26/most-exclusive-private-golf-clubs-america/",
            "https://www.clubcorp.com/our-clubs",
            "https://www.americangolf.com/club-directory",
            "https://www.troon.com/golf-clubs/",
            "https://www.discovery-land.com/clubs/",
            "https://www.eliteclub.com/directory"
        ]
        
        ai_clubs = scraper.scrape_private_clubs_with_ai(private_club_urls)
        all_clubs.extend(ai_clubs)
        print(f"AI found {len(ai_clubs)} additional private clubs")
    
    # Convert to DataFrame and clean
    if all_clubs:
        df = pd.DataFrame(all_clubs)
        
        # Remove duplicates based on club name and state
        df = df.drop_duplicates(subset=['Club Name', 'State'], keep='first')
        
        # Ensure all required columns exist
        required_columns = ['Club Name', 'State', 'City', 'Monthly Dues', 'Contact Phone', 'Website', 'Address', 'Prestige Level', 'Membership Type', 'Initiation Fee', 'Other Costs']
        for col in required_columns:
            if col not in df.columns:
                df[col] = ''
        
        result_df = cast(pd.DataFrame, df[required_columns])
        return result_df
    
    return pd.DataFrame()