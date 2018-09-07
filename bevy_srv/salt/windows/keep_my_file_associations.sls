---
# Salt state for preventing Windows 10 applications from stealing file type associations.
#
#Windows Registry Editor Version 5.00
#
#;Description: Prevents Windows 10 from resetting the file associations
#;... by adding NoOpenWith & NoStaticDefaultVerb values for all the modern apps.
#;Created on Feb 13 2016 by Ramesh Srinivasan
#;Updated on Sep 28 2016
#;The Winhelponline Blog
#;http://www.winhelponline.com/blog
#;Tested in Windows 10 v1511 & 1607
#
{% if grains['os'] == 'Windows' and grains['osrelease'] == '10' %}
#;-------------------
#;Microsoft.3DBuilder
#;-------------------
#;File Types: .stl, .3mf, .obj, .wrl, .ply, .fbx, .3ds, .dae, .dxf, .bmp
#;... .jpg, .png, .tga
#[HKEY_CURRENT_USER\SOFTWARE\Classes\AppXvhc4p7vz4b485xfp46hhk3fq3grkdgjg]
#"NoOpenWith"=""
#"NoStaticDefaultVerb"=""
HKEY_CURRENT_USER\SOFTWARE\Classes\AppXvhc4p7vz4b485xfp46hhk3fq3grkdgjg:
  reg.present:
    - vname: NoOpenWith
    - vdata: ''
2_HKEY_CURRENT_USER\SOFTWARE\Classes\AppXvhc4p7vz4b485xfp46hhk3fq3grkdgjg:
  reg.present:
    - name: HKEY_CURRENT_USER\SOFTWARE\Classes\AppXvhc4p7vz4b485xfp46hhk3fq3grkdgjg
    - vname: NoStaticDefaultVerb
    - vdata: ''
    - vtype: REG_SZ
#
#;-------------------
#;Microsoft Edge
#;-------------------
#;File Types: .htm, .html
HKEY_CURRENT_USER\SOFTWARE\Classes\AppX4hxtad77fbk3jkkeerkrm0ze94wjf3s9:
  reg.present:
    - vname: NoOpenWith
    - vdata: ''
2_HKEY_CURRENT_USER\SOFTWARE\Classes\AppX4hxtad77fbk3jkkeerkrm0ze94wjf3s9:
  reg.present:
    - name: HKEY_CURRENT_USER\SOFTWARE\Classes\AppX4hxtad77fbk3jkkeerkrm0ze94wjf3s9
    - vname: NoStaticDefaultVerb
    - vdata: ''
    - vtype: REG_SZ
#;File Types: .pdf
HKEY_CURRENT_USER\SOFTWARE\Classes\AppXd4nrz8ff68srnhf9t5a8sbjyar1cr723:
  reg.present:
    - vname: NoOpenWith
    - vdata: ''
2_HKEY_CURRENT_USER\SOFTWARE\Classes\AppXd4nrz8ff68srnhf9t5a8sbjyar1cr723:
  reg.present:
    - name: HKEY_CURRENT_USER\SOFTWARE\Classes\AppXd4nrz8ff68srnhf9t5a8sbjyar1cr723
    - vname: NoStaticDefaultVerb
    - vdata: ''
    - vtype: REG_SZ
#
#;File Types: .svg
HKEY_CURRENT_USER\SOFTWARE\Classes\AppXde74bfzw9j31bzhcvsrxsyjnhhbq66cs:
  reg.present:
    - vname: NoOpenWith
    - vdata: ''
2_HKEY_CURRENT_USER\SOFTWARE\Classes\AppXde74bfzw9j31bzhcvsrxsyjnhhbq66cs:
  reg.present:
    - name: HKEY_CURRENT_USER\SOFTWARE\Classes\AppXvhc4p7vz4b485xfp46hhk3fq3grkdgjg
    - vname: NoStaticDefaultVerb
    - vdata: ''
    - vtype: REG_SZ
#
#;File Types: .xml
HKEY_CURRENT_USER\SOFTWARE\Classes\AppXcc58vyzkbjbs4ky0mxrmxf8278rk9b3t:
  reg.present:
    - vname: NoOpenWith
    - vdata: ''
2_HKEY_CURRENT_USER\SOFTWARE\Classes\AppXcc58vyzkbjbs4ky0mxrmxf8278rk9b3t:
  reg.present:
    - name: HKEY_CURRENT_USER\SOFTWARE\Classes\AppXvhc4p7vz4b485xfp46hhk3fq3grkdgjg
    - vname: NoStaticDefaultVerb
    - vdata: ''
    - vtype: REG_SZ
#
#;-------------------
#;Microsoft Photos
#;-------------------
#;File Types: .3g2,.3gp, .3gp2, .3gpp, .asf, .avi, .m2t, .m2ts, .m4v, .mkv
#;... .mov, .mp4, mp4v, .mts, .tif, .tiff, .wmv
HKEY_CURRENT_USER\SOFTWARE\Classes\AppXk0g4vb8gvt7b93tg50ybcy892pge6jmt:
  reg.present:
    - vname: NoOpenWith
    - vdata: ''
2_HKEY_CURRENT_USER\SOFTWARE\Classes\AppXk0g4vb8gvt7b93tg50ybcy892pge6jmt:
  reg.present:
    - name: HKEY_CURRENT_USER\SOFTWARE\Classes\AppXvhc4p7vz4b485xfp46hhk3fq3grkdgjg
    - vname: NoStaticDefaultVerb
    - vdata: ''
    - vtype: REG_SZ
#
#;File Types: Most Image File Types
HKEY_CURRENT_USER\SOFTWARE\Classes\AppX43hnxtbyyps62jhe9sqpdzxn1790zetc:
  reg.present:
    - vname: NoOpenWith
    - vdata: ''
2_HKEY_CURRENT_USER\SOFTWARE\Classes\AppX43hnxtbyyps62jhe9sqpdzxn1790zetc:
  reg.present:
    - name: HKEY_CURRENT_USER\SOFTWARE\Classes\AppXvhc4p7vz4b485xfp46hhk3fq3grkdgjg
    - vname: NoStaticDefaultVerb
    - vdata: ''
    - vtype: REG_SZ
#
#;File Types: .raw, .rwl, .rw2 and others
HKEY_CURRENT_USER\SOFTWARE\Classes\AppX9rkaq77s0jzh1tyccadx9ghba15r6t3h:
  reg.present:
    - vname: NoOpenWith
    - vdata: ''
2_HKEY_CURRENT_USER\SOFTWARE\Classes\AppX9rkaq77s0jzh1tyccadx9ghba15r6t3h:
  reg.present:
    - name: HKEY_CURRENT_USER\SOFTWARE\Classes\AppXvhc4p7vz4b485xfp46hhk3fq3grkdgjg
    - vname: NoStaticDefaultVerb
    - vdata: ''
    - vtype: REG_SZ
#
#;-------------------
#; Zune Music
#;-------------------
#;File Types: .aac, .adt, .adts ,.amr, .flac, .m3u, .m4a, .m4r, .mp3, .mpa
#;.. .wav, .wma, .wpl, .zpl
HKEY_CURRENT_USER\SOFTWARE\Classes\AppXqj98qxeaynz6dv4459ayz6bnqxbyaqcs:
  reg.present:
    - vname: NoOpenWith
    - vdata: ''
2_HKEY_CURRENT_USER\SOFTWARE\Classes\AppXqj98qxeaynz6dv4459ayz6bnqxbyaqcs:
  reg.present:
    - name: HKEY_CURRENT_USER\SOFTWARE\Classes\AppXvhc4p7vz4b485xfp46hhk3fq3grkdgjg
    - vname: NoStaticDefaultVerb
    - vdata: ''
    - vtype: REG_SZ
#
#;-------------------
#; Zune Video
#;-------------------
#;File Types: .3g2,.3gp, .3gpp, .avi, .divx, .m2t, .m2ts, .m4v, .mkv, .mod
#;... .mov, .mp4, mp4v, .mpe, .mpeg, .mpg, .mpv2, .mts, .tod, .ts
#;... .tts, .wm, .wmv, .xvid
HKEY_CURRENT_USER\SOFTWARE\Classes\AppX6eg8h5sxqq90pv53845wmnbewywdqq5h:
  reg.present:
    - vname: NoOpenWith
    - vdata: ''
2_HKEY_CURRENT_USER\SOFTWARE\Classes\AppX6eg8h5sxqq90pv53845wmnbewywdqq5h:
  reg.present:
    - name: HKEY_CURRENT_USER\SOFTWARE\Classes\AppX6eg8h5sxqq90pv53845wmnbewywdqq5h
    - vname: NoStaticDefaultVerb
    - vdata: ''
    - vtype: REG_SZ
{% endif %}
...
