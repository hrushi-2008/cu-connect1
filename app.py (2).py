import streamlit as st
from storage import load_network, save_network

st.set_page_config(page_title="CU-Connect | Chanakya University", layout="wide")

if "net" not in st.session_state:
    st.session_state.net = load_network()
if "viewing_profile" not in st.session_state:
    st.session_state.viewing_profile = None
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "signin"
if "auth_notice" not in st.session_state:
    st.session_state.auth_notice = ""
if "editing_profile" not in st.session_state:
    st.session_state.editing_profile = False

net = st.session_state.net

# Restore login session across browser refreshes via URL query parameter
if "current_user" not in st.session_state or st.session_state.current_user is None:
    saved_user = st.query_params.get("user", None)
    if saved_user and saved_user in net.users:
        st.session_state.current_user = saved_user
    else:
        st.session_state.current_user = None

# ==========================================
# 1. AUTHENTICATION FLOW (SIGN IN FIRST)
# ==========================================
if not st.session_state.current_user:
    st.title("🎓 CU-Connect: Chanakya University Network")

    if st.session_state.auth_mode == "signin":
        st.subheader("Sign In to Your Account")
        if st.session_state.auth_notice:
            st.success(st.session_state.auth_notice)
            st.session_state.auth_notice = ""

        u_in = st.text_input("Username", key="login_u")
        p_in = st.text_input("Password", type="password", key="login_p")
        if st.button("Sign In", type="primary"):
            if net.login(u_in, p_in):
                clean_u = u_in.strip().lower()
                st.session_state.current_user = clean_u
                st.query_params["user"] = clean_u
                st.rerun()
            else:
                st.error("Invalid username or password.")

        st.divider()
        st.write("Don't have an account yet?")
        if st.button("Create a new account"):
            st.session_state.auth_mode = "signup"
            st.rerun()

    elif st.session_state.auth_mode == "signup":
        st.subheader("Create a New Student Account")
        new_u = st.text_input("Choose Unique Username (no spaces)")
        new_p = st.text_input("Choose Password", type="password")
        new_name = st.text_input("Full Name")
        new_prog = st.selectbox("Programme", ["B.Tech CSAI", "B.Tech EVE", "B.Tech EECS", "BCA", "MCA"])
        new_year = st.selectbox("Year", [1, 2, 3, 4])
        new_bio = st.text_area("Short Bio")

        preset_skills = ["Python", "C++", "Java", "DSA", "PyTorch", "React", "SQL", "Arduino", "Verilog", "MATLAB", "Other"]
        selected_skills = st.multiselect("Select Your Skills", preset_skills)
        custom_skills = []
        if "Other" in selected_skills:
            other_input = st.text_input("Enter other skills (comma-separated, e.g. Rust, Figma, Docker)")
            custom_skills = [s.strip() for s in other_input.split(",") if s.strip()]

        final_skills = [s for s in selected_skills if s != "Other"] + custom_skills

        col_sub, col_back = st.columns([1, 4])
        with col_sub:
            if st.button("Create Account", type="primary"):
                ok, msg = net.signup(new_u, new_p, new_name, new_prog, new_year, new_bio, final_skills)
                if ok:
                    save_network(net)
                    st.session_state.auth_notice = f"✅ Account '{new_u.strip().lower()}' created! Please sign in below."
                    st.session_state.auth_mode = "signin"
                    st.rerun()
                else:
                    st.error(msg)
        with col_back:
            if st.button("← Back to Sign In"):
                st.session_state.auth_mode = "signin"
                st.rerun()
    st.stop()

# ==========================================
# 2. ADMIN DASHBOARD
# ==========================================
me = st.session_state.current_user
if me not in net.users:
    st.session_state.current_user = None
    st.query_params.clear()
    st.rerun()

user_obj = net.users[me]

if user_obj.is_admin:
    top_l, top_r = st.columns([4, 1])
    with top_l:
        st.title("🛡️ CU-Connect Admin Dashboard")
        st.caption(f"Signed in as System Administrator (@{me})")
    with top_r:
        if st.button("Logout", key="adm_logout"):
            st.session_state.current_user = None
            st.session_state.auth_mode = "signin"
            st.query_params.clear()
            st.rerun()

    student_users = [u for u, obj in net.users.items() if not obj.is_admin]
    total_edges = sum(len(friends) for friends in net.adj_list.values()) // 2
    total_posts = sum(len(posts) for posts in net.user_posts.values())
    total_groups = len(net.groups)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Student Nodes (V)", len(student_users))
    m2.metric("Undirected Edges (E)", total_edges)
    m3.metric("Total Posts", total_posts)
    m4.metric("Active Groups", total_groups)

    st.divider()
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["👥 Users", "📝 Posts", "🔗 Edges & Groups"])

    with admin_tab1:
        st.subheader("Registered Student Accounts")
        for u in sorted(student_users):
            u_info = net.users[u]
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"**{u_info.name}** (`@{u}`) — {u_info.programme}, Year {u_info.year}")
                c1.caption(f"Bio: {u_info.bio} | Skills: {', '.join(u_info.skills)} | Connections: {len(net.adj_list[u])}")
                if c2.button("Delete User", key=f"adm_del_u_{u}", type="primary"):
                    net.delete_user_account(u)
                    save_network(net)
                    st.toast(f"Deleted user @{u}")
                    st.rerun()

    with admin_tab2:
        st.subheader("All Posts Across Campus")
        all_posts = [p for posts in net.user_posts.values() for p in posts]
        all_posts.sort(key=lambda x: x["timestamp"], reverse=True)
        if not all_posts:
            st.info("No posts in the database.")
        for p in all_posts:
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"**@{p['author']}** • _{p['time_str']}_ • ❤️ {len(p.get('likes', set()))} | 💬 {len(p.get('comments', []))}")
                c1.write(p["content"])
                if c2.button("Delete Post", key=f"adm_del_p_{p['id']}"):
                    net.delete_post(p["author"], p["id"])
                    save_network(net)
                    st.toast("Post removed.")
                    st.rerun()

    with admin_tab3:
        st.subheader("Active Undirected Connections (Edges)")
        seen_edges = set()
        for u, friends in net.adj_list.items():
            for v in friends:
                edge = tuple(sorted((u, v)))
                if edge not in seen_edges:
                    seen_edges.add(edge)
                    c1, c2 = st.columns([4, 1])
                    c1.write(f"🔗 **`@{edge[0]}`** $\leftrightarrow$ **`@{edge[1]}`**")
                    if c2.button("Remove Edge", key=f"adm_edge_{edge[0]}_{edge[1]}"):
                        net.remove_connection(edge[0], edge[1])
                        save_network(net)
                        st.rerun()

        st.divider()
        st.subheader("Campus Groups")
        for gid, grp in list(net.groups.items()):
            c1, c2 = st.columns([4, 1])
            c1.write(f"👥 **{grp['name']}** ({grp['topic']}) — Members: {', '.join(sorted(grp['members']))}")
            if c2.button("Delete Group", key=f"adm_grp_{gid}"):
                net.groups.pop(gid, None)
                save_network(net)
                st.rerun()
    st.stop()

# ==========================================
# 3. REGULAR STUDENT DASHBOARD
# ==========================================
hdr_l, hdr_r = st.columns([4, 1])
with hdr_l:
    st.markdown(f"### 👋 {user_obj.name} (`@{me}`)")
    st.caption(f"{user_obj.programme} • Year {user_obj.year} • {len(net.adj_list[me])} Connections")
with hdr_r:
    if st.button("Logout", key="top_logout"):
        st.session_state.current_user = None
        st.session_state.viewing_profile = None
        st.session_state.editing_profile = False
        st.session_state.auth_mode = "signin"
        st.query_params.clear()
        net.nav_stack.clear()
        st.rerun()

# --- NOTIFICATIONS PANEL (FIFO DEQUE) ---
user_notifs = net.get_notifications(me)
with st.expander(f"🔔 Notifications ({len(user_notifs)} unread)", expanded=len(user_notifs) > 0):
    if not user_notifs:
        st.caption("No new notifications.")
    else:
        for note in user_notifs:
            st.write(f"• {note}")
        if st.button("✅ Mark all as read", key="clear_notifs"):
            net.clear_notifications(me)
            save_network(net)
            st.rerun()

tab_feed, tab_network, tab_chat, tab_search, tab_profile = st.tabs([
    "🏠 Feed", "🤝 Network", "💬 Chat & Groups", "🔍 Search", "👤 Profile"
])

with tab_feed:
    st.subheader("Share a Project Idea or Update")
    post_text = st.text_area("What are you building?", placeholder="Pitch an idea, ask for lab help, or share progress...")
    post_tags = st.text_input("Tags", placeholder="#CSAI #Hackathon")
    if st.button("Post Update", type="primary") and post_text.strip():
        net.create_post(me, post_text, post_tags)
        save_network(net)
        st.success("Published!")
        st.rerun()

    st.divider()
    st.subheader("Recent Network Posts (K-Way Heap Merged)")
    feed_posts = net.get_home_feed(me)
    if not feed_posts:
        st.info("No posts yet. Connect with peers or publish your first idea!")
    for p in feed_posts:
        if p["author"] not in net.users:
            continue
        author_user = net.users[p["author"]]
        likes_set = p.setdefault("likes", set())
        comments_list = p.setdefault("comments", [])
        is_liked = me in likes_set

        with st.container(border=True):
            st.markdown(f"**{author_user.name}** (`@{p['author']}`) • _{p['time_str']}_")
            st.write(p["content"])
            if p["tags"]:
                st.caption(p["tags"])

            like_label = f"❤️ Liked ({len(likes_set)})" if is_liked else f"🤍 Like ({len(likes_set)})"
            if st.button(like_label, key=f"like_{p['id']}"):
                net.toggle_like(p["author"], p["id"], me)
                save_network(net)
                st.rerun()

            with st.expander(f"💬 Comments ({len(comments_list)})"):
                if not comments_list:
                    st.caption("No comments yet. Start the discussion!")
                for c in comments_list:
                    st.markdown(f"**@{c['author']}** _{c['time_str']}_: {c['text']}")

                c_in, c_btn = st.columns([4, 1])
                with c_in:
                    new_comment = st.text_input(
                        "Write a comment...",
                        key=f"c_in_{p['id']}",
                        label_visibility="collapsed",
                        placeholder="Write a comment...",
                    )
                with c_btn:
                    if st.button("Send", key=f"c_btn_{p['id']}"):
                        if net.add_comment(p["author"], p["id"], me, new_comment):
                            save_network(net)
                            st.rerun()

with tab_network:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"📥 Pending Requests ({len(net.pending_incoming[me])})")
        for sender in list(net.pending_incoming[me]):
            if sender not in net.users:
                continue
            s_user = net.users[sender]
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"**{s_user.name}** (@{sender}) - {s_user.programme}")
            if c2.button("Accept", key=f"acc_{sender}"):
                net.accept_request(me, sender)
                save_network(net)
                st.rerun()
            if c3.button("Reject", key=f"rej_{sender}"):
                net.reject_or_cancel_request(me, sender)
                save_network(net)
                st.rerun()

        st.subheader(f"✅ My Connections ({len(net.adj_list[me])})")
        for friend in sorted(list(net.adj_list[me])):
            if friend not in net.users:
                continue
            f_user = net.users[friend]
            c1, c2 = st.columns([4, 1])
            c1.write(f"**{f_user.name}** (@{friend}) • Skills: {', '.join(f_user.skills)}")
            if c2.button("Remove", key=f"rem_{friend}"):
                net.remove_connection(me, friend)
                save_network(net)
                st.rerun()

    with col2:
        st.subheader("✨ Teammates You May Know (Hybrid Jaccard)")
        recs = net.recommend_teammates(me)
        for cand, score, shared_skills in recs:
            c_user = net.users[cand]
            mutuals = net.get_mutual_connections(me, cand)
            with st.container(border=True):
                st.markdown(f"**{c_user.name}** (`@{cand}`) — Match Score: **{score}**")
                st.caption(f"{c_user.programme} | Mutuals: {len(mutuals)} ({', '.join(mutuals) if mutuals else 'None'}) | Shared Skills: {', '.join(shared_skills) if shared_skills else 'None'}")
                if me in net.pending_incoming[cand]:
                    if st.button("Cancel Request", key=f"can_{cand}"):
                        net.reject_or_cancel_request(cand, me)
                        save_network(net)
                        st.rerun()
                else:
                    if st.button("Connect", key=f"con_{cand}"):
                        ok, msg = net.send_request(me, cand)
                        save_network(net)
                        st.toast(msg)
                        st.rerun()

with tab_chat:
    chat_mode = st.radio(
        "Select Messaging Mode:",
        ["💬 Direct Messages (1-on-1)", "👥 Campus Groups"],
        horizontal=True,
    )

    if chat_mode == "💬 Direct Messages (1-on-1)":
        my_friends = sorted([f for f in net.adj_list[me] if f in net.users])
        if not my_friends:
            st.info("Connect with a classmate in the Network tab first to start chatting!")
        else:
            selected_peer = st.selectbox(
                "Chat With Connection:",
                my_friends,
                format_func=lambda u: f"{net.users[u].name} (@{u})",
            )
            messages = net.get_direct_messages(me, selected_peer)
            with st.container(border=True):
                st.markdown(f"#### Conversation with {net.users[selected_peer].name} (`@{selected_peer}`)")
                if not messages:
                    st.caption("No messages yet. Say hello!")
                for m in messages:
                    if m["sender"] == me:
                        st.markdown(f"**You** _{m['time_str']}_: {m['text']}")
                    else:
                        st.markdown(f"**@{m['sender']}** _{m['time_str']}_: {m['text']}")

            dm_in, dm_btn = st.columns([4, 1])
            with dm_in:
                dm_text = st.text_input(
                    "Type a message...",
                    key=f"dm_input_{selected_peer}",
                    label_visibility="collapsed",
                    placeholder=f"Message @{selected_peer}...",
                )
            with dm_btn:
                if st.button("Send", key=f"dm_send_{selected_peer}", type="primary"):
                    ok, msg = net.send_direct_message(me, selected_peer, dm_text)
                    if ok:
                        save_network(net)
                        st.rerun()
                    else:
                        st.error(msg)

    else:
        with st.expander("➕ Create a New Group", expanded=False):
            grp_name = st.text_input("Group Name (e.g. Smart India Hackathon Team)")
            grp_topic = st.text_input("Topic / Purpose", placeholder="Project collaboration, study group, club...")
            my_friends = sorted([f for f in net.adj_list[me] if f in net.users])
            selected_members = st.multiselect(
                "Add Connections to Group:",
                my_friends,
                format_func=lambda u: f"{net.users[u].name} (@{u})",
            )
            if st.button("Create Group", type="primary"):
                ok, msg = net.create_group(me, grp_name, grp_topic, selected_members)
                if ok:
                    save_network(net)
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

        my_groups = net.get_user_groups(me)
        if not my_groups:
            st.info("You are not in any groups yet. Create one above or ask a connection to add you!")
        else:
            group_map = {g["id"]: g for g in my_groups}
            selected_gid = st.selectbox(
                "Select Your Group:",
                list(group_map.keys()),
                format_func=lambda gid: f"{group_map[gid]['name']} ({len(group_map[gid]['members'])} members)",
            )
            active_group = group_map[selected_gid]

            with st.container(border=True):
                g_hdr_l, g_hdr_r = st.columns([4, 1])
                with g_hdr_l:
                    st.markdown(f"#### 👥 {active_group['name']}")
                    st.caption(f"Topic: {active_group['topic']} | Members: {', '.join('@' + m for m in sorted(active_group['members']))}")
                with g_hdr_r:
                    if st.button("Leave Group", key=f"leave_grp_{selected_gid}"):
                        net.leave_group(selected_gid, me)
                        save_network(net)
                        st.rerun()

                addable = sorted([f for f in net.adj_list[me] if f in net.users and f not in active_group["members"]])
                if addable:
                    add_c1, add_c2 = st.columns([3, 1])
                    with add_c1:
                        to_add = st.selectbox(
                            "Add member",
                            addable,
                            key=f"add_sel_{selected_gid}",
                            label_visibility="collapsed",
                            format_func=lambda u: f"Add {net.users[u].name} (@{u})",
                        )
                    with add_c2:
                        if st.button("Add", key=f"add_btn_{selected_gid}"):
                            ok, msg = net.add_group_member(selected_gid, me, to_add)
                            if ok:
                                save_network(net)
                                st.rerun()

                st.divider()
                for gm in active_group["messages"]:
                    if gm["sender"] == "system":
                        st.caption(f"ℹ️ {gm['text']} ({gm['time_str']})")
                    elif gm["sender"] == me:
                        st.markdown(f"**You** _{gm['time_str']}_: {gm['text']}")
                    else:
                        st.markdown(f"**@{gm['sender']}** _{gm['time_str']}_: {gm['text']}")

            g_in, g_btn = st.columns([4, 1])
            with g_in:
                g_text = st.text_input(
                    "Group message...",
                    key=f"grp_in_{selected_gid}",
                    label_visibility="collapsed",
                    placeholder=f"Message {active_group['name']}...",
                )
            with g_btn:
                if st.button("Send", key=f"grp_send_{selected_gid}", type="primary"):
                    ok, msg = net.send_group_message(selected_gid, me, g_text)
                    if ok:
                        save_network(net)
                        st.rerun()
                    else:
                        st.error(msg)

with tab_search:
    st.subheader("🔍 Real-Time Prefix Search (Trie)")
    search_mode = st.radio(
        "Search Students By:",
        ["Name or Username", "Technical Skill"],
        horizontal=True,
    )

    if search_mode == "Name or Username":
        query = st.text_input("Type a student's name or username prefix (e.g. 'a', 'di', 'ro'):")
        results = net.search_users(query) if query else []
    else:
        query = st.text_input("Type a skill prefix (e.g. 'py', 'ard', 'mat', 'ver'):")
        results = net.search_by_skill(query) if query else []

    if query:
        st.write(f"Found {len(results)} match(es):")
        for r in results:
            skills_preview = ", ".join(r.skills) if r.skills else "No skills listed"
            if st.button(f"View Profile: {r.name} (@{r.username}) — [{skills_preview}]", key=f"view_{r.username}"):
                if st.session_state.viewing_profile and st.session_state.viewing_profile != r.username:
                    net.nav_stack.append(st.session_state.viewing_profile)
                st.session_state.viewing_profile = r.username
                st.rerun()

    if st.session_state.viewing_profile and st.session_state.viewing_profile in net.users:
        target = st.session_state.viewing_profile
        t_user = net.users[target]
        st.divider()
        if net.nav_stack and net.nav_stack[-1] in net.users:
            if st.button(f"⬅ Back to @{net.nav_stack[-1]} (Stack Pop)"):
                st.session_state.viewing_profile = net.nav_stack.pop()
                st.rerun()

        st.markdown(f"### Profile: {t_user.name} (`@{target}`)")
        st.write(f"**Programme:** {t_user.programme} (Year {t_user.year}) | **Bio:** {t_user.bio}")
        st.write(f"**Skills:** {', '.join(t_user.skills)}")

        if target != me:
            deg, path = net.find_shortest_path_bfs(me, target)
            mutuals = net.get_mutual_connections(me, target)
            if deg != -1:
                st.success(f"**Degree of Connection:** {deg} | **Shortest Chain (BFS):** {' ➔ '.join(path)}")
            else:
                st.warning("No connection path exists yet.")
            st.info(f"**Mutual Connections ({len(mutuals)}):** {', '.join(mutuals) if mutuals else 'None'}")

with tab_profile:
    st.subheader("🪪 Account Holder Details")
    with st.container(border=True):
        st.markdown(f"### {user_obj.name}")
        st.write(f"**Username:** `@{me}`")
        st.write(f"**Programme:** {user_obj.programme}")
        st.write(f"**Year:** Year {user_obj.year}")
        st.write(f"**Bio:** {user_obj.bio if user_obj.bio else 'No bio added yet.'}")
        st.write(f"**Skills:** {', '.join(user_obj.skills) if user_obj.skills else 'None'}")
        st.write(f"**Total Connections:** {len(net.adj_list[me])}")

        if st.button("✏️ Edit Profile Details"):
            st.session_state.editing_profile = not st.session_state.editing_profile
            st.rerun()

    if st.session_state.editing_profile:
        with st.container(border=True):
            st.subheader("Edit Your Profile")
            edit_name = st.text_input("Full Name", value=user_obj.name)
            prog_options = ["B.Tech CSAI", "B.Tech EVE", "B.Tech EECS", "BCA", "MCA"]
            prog_idx = prog_options.index(user_obj.programme) if user_obj.programme in prog_options else 0
            edit_prog = st.selectbox("Programme", prog_options, index=prog_idx)
            year_options = [1, 2, 3, 4]
            year_idx = year_options.index(user_obj.year) if user_obj.year in year_options else 0
            edit_year = st.selectbox("Year", year_options, index=year_idx)
            edit_bio = st.text_area("Short Bio", value=user_obj.bio)

            preset_skills = ["Python", "C++", "Java", "DSA", "PyTorch", "React", "SQL", "Arduino", "Verilog", "MATLAB", "Other"]
            existing_presets = [s for s in user_obj.skills if s in preset_skills and s != "Other"]
            existing_custom = [s for s in user_obj.skills if s not in preset_skills]
            if existing_custom:
                existing_presets.append("Other")

            edit_selected = st.multiselect("Select Your Skills", preset_skills, default=existing_presets)
            edit_custom = []
            if "Other" in edit_selected:
                other_val = st.text_input("Other skills (comma-separated)", value=", ".join(existing_custom))
                edit_custom = [s.strip() for s in other_val.split(",") if s.strip()]

            updated_skills = [s for s in edit_selected if s != "Other"] + edit_custom

            c_save, c_cancel = st.columns([1, 4])
            with c_save:
                if st.button("Save Changes", type="primary"):
                    ok, msg = net.update_profile(me, edit_name, edit_prog, edit_year, edit_bio, updated_skills)
                    if ok:
                        save_network(net)
                        st.session_state.editing_profile = False
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            with c_cancel:
                if st.button("Cancel"):
                    st.session_state.editing_profile = False
                    st.rerun()

    st.divider()
    st.subheader("📝 My Published Posts")
    my_posts = list(reversed(net.user_posts[me]))
    if not my_posts:
        st.write("You haven't posted anything yet.")
    for p in my_posts:
        with st.container(border=True):
            st.write(p["content"])
            st.caption(f"{p['time_str']} {p['tags']} • ❤️ {len(p.get('likes', set()))} | 💬 {len(p.get('comments', []))}")
            if st.button("Delete Post", key=f"del_{p['id']}"):
                net.delete_post(me, p["id"])
                save_network(net)
                st.rerun()

    st.divider()
    with st.expander("⚠️ Danger Zone: Delete Account"):
        st.warning("Deleting your profile permanently removes your account, connections, pending requests, and posts from the network.")
        confirm_del = st.checkbox("I confirm I want to permanently delete my account.")
        if st.button("Delete My Profile", type="primary", disabled=not confirm_del):
            net.delete_user_account(me)
            save_network(net)
            st.session_state.current_user = None
            st.session_state.viewing_profile = None
            st.session_state.editing_profile = False
            st.session_state.auth_mode = "signin"
            st.session_state.auth_notice = f"Your account '@{me}' has been permanently deleted."
            st.query_params.clear()
            st.rerun()