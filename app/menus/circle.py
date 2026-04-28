from datetime import datetime
import json
from app.menus.package import get_packages_by_family, show_package_details
from app.menus.util import pause, clear_screen, format_quota_byte
from app.client.circle import (
    get_group_data,
    get_group_members,
    create_circle,
    validate_circle_member,
    invite_circle_member,
    remove_circle_member,
    accept_circle_invitation,
    spending_tracker,
    get_bonus_data,
    get_circle_oc, # Import tambahan untuk Family Hub
)
from app.service.auth import AuthInstance
from app.client.encrypt import decrypt_circle_msisdn, decrypt_xdata

WIDTH = 55

def show_family_hub_store(api_key: str, tokens: dict, parent_subs_id: str, group_id: str):
    """Bypass Family Hub Store - Menampilkan paket yang tersedia"""
    clear_screen()
    print("=" * WIDTH)
    print("FAMILY HUB STORE (BYPASS)".center(WIDTH))
    print("=" * WIDTH)
    
    res = get_circle_oc(api_key, tokens, parent_subs_id, group_id)
    if "xdata" in res:
        res = decrypt_xdata(api_key, res)

    if res.get("status") == "FAILED" or "data" not in res:
        print(f"❌ Error: {res.get('message', 'Gagal mengambil data store.')}")
        pause(); return

    packages = res.get("data", {}).get("packages", [])
    if not packages:
        print("❌ Tidak ada paket tersedia."); pause(); return

    print("-" * WIDTH)
    for pkg in packages:
        name = pkg.get("package_name", "N/A")
        code = pkg.get("package_option_code", "N/A")
        price = pkg.get("price", "N/A")
        print(f"📦 NAME : {name}")
        print(f"🔑 CODE : {code}")
        if price != "N/A": print(f"💰 PRICE: {price}")
        print("-" * WIDTH)

    print("[!] Selesai menampilkan daftar paket.")
    pause()

def show_bonus_list(api_key: str, tokens: dict, parent_subs_id: str, family_id: str):
    in_circle_bonus_menu = True
    while in_circle_bonus_menu:
        clear_screen()
        print("🔄 Fetching bonus data...")
        bonus_data = get_bonus_data(api_key, tokens, parent_subs_id, family_id)
        
        if bonus_data.get("status") != "SUCCESS":
            print("❌ Failed to fetch bonus data.")
            pause(); return
        
        bonus_list = bonus_data.get("data", {}).get("bonuses", [])
        if not bonus_list:
            print("❌ No bonus data available."); pause(); return
        
        print("=" * WIDTH)
        print("CIRCLE BONUS LIST".center(WIDTH))
        print("=" * WIDTH)
        
        for idx, bonus in enumerate(bonus_list, start=1):
            print(f"{idx}. {bonus.get('name', 'N/A')} | Type: {bonus.get('bonus_type', 'N/A')}")
            print(f"   Action: {bonus.get('action_type', 'N/A')} | Param: {bonus.get('action_param', 'N/A')}")
            
        print("-" * WIDTH)
        print("00. Back")
        
        choice = input("\nPilih nomor bonus untuk detail (atau 00): ")
        if choice == "00":
            in_circle_bonus_menu = False
        else:
            try:
                idx = int(choice) - 1
                selected_bonus = bonus_list[idx]
                action_type = selected_bonus.get("action_type", "N/A")
                action_param = selected_bonus.get("action_param", "N/A")
                
                if action_type == "PLP":
                    get_packages_by_family(action_param)
                elif action_type == "PDP":
                    show_package_details(api_key, tokens, action_param, False)
                else:
                    print(f"Unhandled Action Type: {action_type}")
                    pause()
            except:
                print("Input tidak valid."); pause()

def show_circle_creation(api_key: str, tokens: dict):
    clear_screen()
    print("CREATE NEW CIRCLE".center(WIDTH))
    print("-" * WIDTH)
    p_name = input("Nama Anda (Parent): ")
    g_name = input("Nama Circle: ")
    m_msisdn = input("MSISDN Member (contoh: 6281xxx): ")
    m_name = input("Nama Member: ")
    
    res = create_circle(api_key, tokens, p_name, g_name, m_msisdn, m_name)
    print("\nServer Response:")
    print(json.dumps(res, indent=2))
    pause()

def show_circle_info(api_key: str, tokens: dict):
    in_circle_menu = True
    user = AuthInstance.get_active_user()
    my_msisdn = user.get("number", "")

    while in_circle_menu:
        clear_screen()
        group_res = get_group_data(api_key, tokens)
        if group_res.get("status") != "SUCCESS":
            print("❌ Failed to fetch circle data."); pause(); return
        
        group_data = group_res.get("data", {})        
        group_id = group_data.get("group_id", "")

        if not group_id:
            print("You are not part of any Circle.")
            if input("Create new? (y/n): ").lower() == "y":
                show_circle_creation(api_key, tokens)
                continue
            return
        
        # Ambil Data Member & Spending
        members_res = get_group_members(api_key, tokens, group_id)
        members_data = members_res.get("data", {})
        members = members_data.get("members", [])
        
        parent_subs_id = ""
        parent_member_id = ""
        for m in members:
            if m.get("member_role") == "PARENT":
                parent_subs_id = m.get("subscriber_number", "")
                parent_member_id = m.get("member_id", "")

        spending_res = spending_tracker(api_key, tokens, parent_subs_id, group_id)
        spending_data = spending_res.get("data", {})

        # Tampilkan Header & Info Kuota
        package = members_data.get("package", {})
        benefit = package.get("benefit", {})
        
        print("=" * WIDTH)
        print(f"CIRCLE: {group_data.get('group_name')} ({group_data.get('group_status')})".center(WIDTH))
        print(f"Package: {package.get('name')} | {format_quota_byte(benefit.get('remaining',0))} / {format_quota_byte(benefit.get('allocation',0))}".center(WIDTH))
        print(f"Spending: Rp{spending_data.get('spend',0):,} / Rp{spending_data.get('target',0):,}".center(WIDTH))
        print("=" * WIDTH)
        
        for idx, m in enumerate(members, start=1):
            msisdn = decrypt_circle_msisdn(api_key, m.get("msisdn", ""))
            role = "Parent" if m.get("member_role") == "PARENT" else "Member"
            me = "(You)" if str(msisdn) == str(my_msisdn) else ""
            print(f"{idx}. {msisdn} ({m.get('member_name')}) | {role} {me}")
            print(f"   Usage: {format_quota_byte(m.get('allocation',0)-m.get('remaining',0))} / {format_quota_byte(m.get('allocation',0))} | Status: {m.get('status')}")
            print("-" * WIDTH)

        print("\nOPTIONS:")
        print("1. Invite Member")
        print("2. Bonus List")
        print("3. FAMILY HUB")
        print("del <no> - Hapus Member")
        print("acc <no> - Terima Undangan")
        print("00. Back")
        
        choice = input("\n>> ")
        
        if choice == "00":
            in_circle_menu = False
        elif choice == "1":
            target_msisdn = input("MSISDN target: ")
            target_name = input("Nama target: ")
            res = invite_circle_member(api_key, tokens, target_msisdn, target_name, group_id, parent_member_id)
            print(json.dumps(res, indent=2)); pause()
        elif choice == "2":
            show_bonus_list(api_key, tokens, parent_subs_id, group_id)
        elif choice == "3":
            show_family_hub_store(api_key, tokens, parent_subs_id, group_id)
        elif choice.startswith("del "):
            try:
                idx = int(choice.split(" ")[1]) - 1
                m_id = members[idx].get("member_id")
                res = remove_circle_member(api_key, tokens, m_id, group_id, parent_member_id, len(members) == 2)
                print(json.dumps(res, indent=2)); pause()
            except: print("Gagal hapus."); pause()
        elif choice.startswith("acc "):
            try:
                idx = int(choice.split(" ")[1]) - 1
                m_id = members[idx].get("member_id")
                res = accept_circle_invitation(api_key, tokens, group_id, m_id)
                print(json.dumps(res, indent=2)); pause()
            except: print("Gagal accept."); pause()
