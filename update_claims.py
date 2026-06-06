from pathlib import Path

# Read the original file
file_path = Path(r'c:\Users\ABCJ\Desktop\lawforms\forms\templates\forms\application_divorce_8a_page4.html')
content = file_path.read_text(encoding='utf-8')

# Find the section to replace - from "<!-- CLAIMS -->" to before "Important Facts"
start_idx = content.find('  <!-- CLAIMS -->')
end_idx = content.find('  <div class="card shadow-sm border-0 mb-4">\n\n    <div class="card-header bg-light fw-bold">\n      Important Facts')

if start_idx == -1 or end_idx == -1:
    print(f"start_idx={start_idx}, end_idx={end_idx}")
    # Try alternative pattern
    end_idx = content.find('  <div class="card shadow-sm border-0 mb-4">')
    # Find the second occurrence (first is Other Claims, second is Important Facts)
    first_idx = content.find('  <div class="card shadow-sm border-0 mb-4">', start_idx + 10)
    second_idx = content.find('  <div class="card shadow-sm border-0 mb-4">', first_idx + 10)
    print(f"Trying: first_idx={first_idx}, second_idx={second_idx}")
    if second_idx > 0:
        end_idx = second_idx

print(f"Will replace from {start_idx} to {end_idx}")
print(f"Content length: {len(content)}")

if start_idx > 0 and end_idx > start_idx:
    new_claims = '''  <!-- CLAIMS FRAME FOR JOINT APPLICATION -->
  <div style="border: 2px solid #0f172a; border-radius: 8px; padding: 20px; margin-bottom: 24px; background: #f8fafc;">
    
    <div style="text-align: center; margin-bottom: 20px;">
      <p style="margin: 0; font-weight: 900; font-size: 13px; color: #0f172a; letter-spacing: 0.05em;">
        USE THIS FRAME ONLY IF THIS CASE IS A JOINT APPLICATION FOR DIVORCE
      </p>
    </div>

    <div style="text-align: center; margin-bottom: 24px;">
      <p style="margin: 0; font-weight: 900; font-size: 14px; color: #0f172a;">
        WE JOINTLY ASK THE COURT FOR THE FOLLOWING:
      </p>
    </div>

    <!-- CLAIMS UNDER THE DIVORCE ACT -->
    <div style="margin-bottom: 24px;">
      <p style="font-weight: 900; font-size: 13px; color: #0f172a; margin: 0 0 12px 0;">Claims under the Divorce Act</p>
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;">
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          {{ form.claim_divorce }}
          <span style="margin-top: 2px;">00 a divorce</span>
        </label>
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          {{ form.claim_spousal_support }}
          <span style="margin-top: 2px;">01 spousal support</span>
        </label>
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          {{ form.claim_child_support_table }}
          <span style="margin-top: 2px;">02 support for child(ren) — table amount</span>
        </label>
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          {{ form.claim_child_support_other }}
          <span style="margin-top: 2px;">03 support for child(ren) — other than table amount</span>
        </label>
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          {{ form.claim_decision_making }}
          <span style="margin-top: 2px;">04 decision-making responsibility for child(ren)</span>
        </label>
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          {{ form.claim_parenting_time }}
          <span style="margin-top: 2px;">05 parenting time with child(ren)</span>
        </label>
      </div>
    </div>

    <!-- CLAIMS UNDER THE FAMILY LAW ACT OR CHILDREN'S LAW REFORM ACT -->
    <div style="margin-bottom: 24px;">
      <p style="font-weight: 900; font-size: 13px; color: #0f172a; margin: 0 0 12px 0;">Claims under the Family Law Act or Children's Law Reform Act</p>
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;">
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          <input type="checkbox" name="claim_spousal_support_family_law" style="margin-top: 3px;">
          <span>10 spousal support</span>
        </label>
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          {{ form.claim_support_child_table_family_law }}
          <span style="margin-top: 2px;">11 support for child(ren) — table amount</span>
        </label>
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          {{ form.claim_support_child_other_family_law }}
          <span style="margin-top: 2px;">12 support for child(ren) — other than table amount</span>
        </label>
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          <input type="checkbox" name="claim_decision_making_family_law" style="margin-top: 3px;">
          <span>13 decision-making responsibility for children</span>
        </label>
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          <input type="checkbox" name="claim_parenting_time_family_law" style="margin-top: 3px;">
          <span>14 parenting time with child(ren)</span>
        </label>
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          {{ form.claim_restraining_order }}
          <span style="margin-top: 2px;">15 restraining/non-harassment order</span>
        </label>
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          {{ form.claim_indexing_spousal_support }}
          <span style="margin-top: 2px;">16 indexing spousal support</span>
        </label>
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          {{ form.claim_declaration_parentage }}
          <span style="margin-top: 2px;">17 declaration of parentage</span>
        </label>
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          {{ form.claim_guardianship_child_property }}
          <span style="margin-top: 2px;">18 guardianship over child's property</span>
        </label>
      </div>
    </div>

    <!-- CLAIMS RELATING TO PROPERTY -->
    <div style="margin-bottom: 24px;">
      <p style="font-weight: 900; font-size: 13px; color: #0f172a; margin: 0 0 12px 0;">Claims relating to property</p>
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;">
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          {{ form.claim_property_equalization }}
          <span style="margin-top: 2px;">20 equalization of net family properties</span>
        </label>
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          {{ form.claim_exclusive_possession_home }}
          <span style="margin-top: 2px;">21 exclusive possession of matrimonial home</span>
        </label>
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          {{ form.claim_exclusive_possession_contents }}
          <span style="margin-top: 2px;">22 exclusive possession of contents of matrimonial home</span>
        </label>
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          {{ form.claim_freezing_assets }}
          <span style="margin-top: 2px;">23 freezing assets</span>
        </label>
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          {{ form.claim_sale_family_property }}
          <span style="margin-top: 2px;">24 sale of family property</span>
        </label>
      </div>
    </div>

    <!-- OTHER CLAIMS -->
    <div>
      <p style="font-weight: 900; font-size: 13px; color: #0f172a; margin: 0 0 12px 0;">Other claims</p>
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 14px;">
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          {{ form.claim_costs }}
          <span style="margin-top: 2px;">30 costs</span>
        </label>
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          {{ form.claim_annulment }}
          <span style="margin-top: 2px;">31 annulment of marriage</span>
        </label>
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          {{ form.claim_prejudgment_interest }}
          <span style="margin-top: 2px;">32 prejudgment interest</span>
        </label>
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px;">
          {{ form.claim_other }}
          <span style="margin-top: 2px;">50 Other (Specify)</span>
        </label>
      </div>

      <div style="margin-top: 12px;">
        <label style="display: block; font-weight: 700; font-size: 12px; color: #0f172a; margin-bottom: 6px;">
          Other claims (specify)
        </label>
        {{ form.other_claims|add_class:"form-control"|attr:"rows:3" }}
      </div>
    </div>

  </div>

'''
    
    new_content = content[:start_idx] + new_claims + content[end_idx:]
    file_path.write_text(new_content, encoding='utf-8')
    print('✓ File updated successfully!')
else:
    print("Could not find replacement boundaries")
