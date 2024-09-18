#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import pandas as pd
import re
import time


# In[2]:


def parse_time_range(time_str):
    if '时间段' in time_str:
        item_split_m = re.split(r'\)\:|\&',time_str)
        
        for i,item in enumerate(item_split_m):
            if i % 2 == 0:
                item_split_m[i] = item_split_m[i] + ')'
    else:
        
        item_split_m = re.split(r'[:&]',time_str)

    return item_split_m
    


# In[3]:


def parse_cell_result(lines_lst ,d,head_list,mml_str,name_str,dict_dd,h_1,key_str):
    #小区级报文转换
    
    info_list = []
    
    if len(head_list) == 2:
        head_list.extend(h_1)
        
    for i in range(6,10000):
        
        item_str = lines_lst[d + i]
        
        if '结果个数' in item_str:
            #print(idx + i ,head,len(head),context,len(context),sep='\n')
            df = pd.DataFrame(data=info_list,columns=head_list)
            export_df(dict_dd,df,key_str)

            break

        else:

            result = re.split(r'\s{2,}',item_str.strip())
            result.insert(0,mml_str)
            result.insert(1,name_str)

            head_str = '*'.join(head_list)

            if '&' not in head_str:
                head_list , result = get_head(head_list , result)
            else:
                result = get_result(result)

            info_list.append(result)


# In[4]:


def parse_gnb_result(lines_lst,d,head_list,mml_str ,name_str ,dict_dd ,key ):
    
    gnb_list = []
    
    gnb_list.extend([mml_str,name_str])

    for i in range(4,10000):
        
        lines_str = lines_lst[d + i]

        if '结果个数' in lines_str:

            df = pd.DataFrame(data=[gnb_list],columns=head_list)
            export_df(dict_dd,df,key)

            break

        else:

            item_split = re.split(r'[=]',lines_str)
            item_split = [val.strip() for val in item_split]

            h,c = item_split

            if ':' not in c or c[-2:] not in [':关',':开']:
                head_list.append(h)
                gnb_list.append(c)
            else:

                item_split_m = parse_time_range(c)

                c_1,c_2 = item_split_m

                if len(item_split_m) != 2:  
                    print(item_split_m)

                if h != '':
                    head_list.append(h + '&' + c_1)
                    switch = h
                else:
                    head_list.append(switch + '&' + c_1)

                gnb_list.append(c_2)


# In[5]:


def get_head(lst_1, lst_2):  
    if len(lst_1) != len(lst_2):  
        return None  
  
    # 创建一个新列表来存储修改后的结果，以避免在迭代时修改原列表  
    new_lst_1 = []  
    new_lst_2 = []  

    for i, (item1, item2) in enumerate(zip(lst_1, lst_2)): 
        if ':' not in item2 or i < 2 or '覆盖等级' in item2 or item2[-2:] not in [':关',':开']:
            new_lst_1.append(item1)  
            new_lst_2.append(item2)  

        else:  

            contents = parse_time_range(item2)
    
            # 奇数索引的内容放入lst_2，偶数索引的内容（除了第一个）与lst_1的元素合并  
            for j, content in enumerate(contents):  
                if j % 2 == 0:  
                    new_lst_1.append(item1 + '&' + content)  
                else:  
                    new_lst_2.append(content) 

    return new_lst_1, new_lst_2  


# In[6]:


def get_result(lst_1):
    #针对小区开关级参数结果，剔除开关名称，获取开关值，返回新列表
    new_list = []
    for i,item in enumerate(lst_1):
        if ':' not in item or '覆盖等级' in item or i < 2 or item[-2:] not in [':关',':开']:
            new_list.append(item)
        else:
            item_split = parse_time_range(item)
            for j,ite in enumerate(item_split):
                if j % 2 != 0: 
                    new_list.append(ite)
               
    return new_list


# In[7]:


def replace_db(db_str):
    return db_str.replace('毫瓦分贝','dBm').replace('分贝','dB')


# In[8]:


def export_df(dic,dataframe ,item):
    if item not in dic:
        dic[item] = dataframe
    else:
        dic[item] = pd.concat([dic[item],dataframe])


# In[9]:


def parse_info_result(lines_lst,d,h_list,mml_str,name_str,dict_dd):
    # 操作日志报文转换
    info_list = []
    h_list.extend(['操作帐号','操作IP地址','操作开始时间','操作结果','操作结束时间','操作MML脚本'])
    
    for i in range(4,10000):
        
        info_str = lines_lst[d + i]
        
        if '结果个数' in info_str:
            df = pd.DataFrame(data=info_list,columns=h_list)
            export_df(dict_dd,df,'查询操作日志')
            break

        elif '域用户' in info_str:
            z_list = re.split(r'\s{2,}',info_str)
            m_list = re.split(r'\*\/',lines_lst[d + i + 1])
                
            zh = z_list[1]
            ip = z_list[3]
            s_time = z_list[5]
            jg = z_list[6]
            e_time = z_list[9]
            
            m = m_list[-1].strip()
            
            info_list.append([mml_str,name_str,zh,ip,s_time,jg,e_time,m])

        else:
            pass


# In[10]:


def get_name_mml_key(lines_list , d ,suc_fail ,dict_dd):
    if suc_fail:
        name = re.split(r'\s{2,}',lines_list[d - 3])[1]        #  报文 : +++    盐城-盐都-凤洋村700M-H5H        2024-09-11 17:40:08
        mml = re.split(r'\*\/',lines_list[d - 1].replace('%%\n',''))[-1]   # %%/*1939662107 MML Session=1726047602*/LST NRDUCELLSERVEXP:;%%
        key = lines_list[d + 2].strip('\n')          # 查询NR小区异系统切换测量参数组

    else:
        name = lines_list[d - 1].split(' : ')[1].strip()
        mml = lines_list[d - 2].split('-')[-1].strip()
        key = lines_list[d].split(' : ')[1].strip()
    
        df = pd.DataFrame(data=[[name,mml,key]],columns=['网元名称','MML命令','报文'])  #思路改为获取每个参数转为df，后面合并
        export_df(dict_dd,df,'异常')
        
    return [name,mml,key]


# In[11]:


def convent_mml(file_path ,dict_dd):

    with open(file_path ,'r') as soruce_txt:
        lines = soruce_txt.readlines()
        for idx,item in enumerate(lines):
            
            if idx % 100000 == 0 and idx != 0:
                print('{} 已完成{}行数据转换......'.format(time.strftime('%Y-%H-%M %S') ,idx ))
            
            head = []

            if '网元断连' in item or '非法命令，不能执行' in item:

                name,mml,key = get_name_mml_key(lines ,idx ,False, dict_dd)

            elif '执行成功' in item:

                name,mml,key = get_name_mml_key(lines ,idx ,True, dict_dd)

                if key == '没有查到相应的结果':
                    df = pd.DataFrame(data=[[name,mml,key]],columns=['网元名称','MML命令','报文'])
                    export_df(dict_dd,df,'异常')
                    continue

                #获取表头
                down_four = lines[idx + 4]

                if '毫瓦分贝' in down_four or '分贝' in down_four:
                    down_four = replace_db(down_four)   #毫瓦分贝调整为dbm、分贝调整为db

                h = re.split(r'\s{2,}',down_four.strip())
                head.extend(['报文MML','网元名称'])

                if '=' in down_four:
                    parse_gnb_result(lines ,idx ,head ,mml ,name , dict_dd ,key)

                elif lines[idx + 2].strip() == '日志信息':
                    parse_info_result(lines, idx, head,mml, name, dict_dd)

                else:
                    parse_cell_result(lines ,idx ,head ,mml ,name ,dict_dd ,h ,key)
                


# In[12]:


def get_txts_path():

    # 获取当前程序所在目录
    current_directory = os.getcwd()
    # 拼接input文件夹的路径
    input_directory = os.path.join(current_directory, 'input')

    # 确保input文件夹存在
    if not os.path.exists(input_directory):
        raise ValueError(f"Directory '{input_directory}' does not exist.")

    # 获取input文件夹中所有.txt文件的地址列表
    txt_files = [os.path.join(input_directory, f) for f in os.listdir(input_directory) if f.endswith('.txt')]

    return txt_files
    


# In[13]:


if __name__ == '__main__':
    
    start_time = time.time()
    
    txt_files = get_txts_path()
    
    dict_mml = {}
    
    for txt_file in txt_files:
        
        convent_mml(txt_file , dict_mml)
    
    end_time = time.time()
    
    duration = end_time - start_time
    
    s = len(dict_mml.keys())
        
    print('本次共计完成{}个参数格式转换,共计耗时{:.2f}秒!'.format(s , duration))
    
    


# In[ ]:





# In[22]:


out_file = os.path.join(os.getcwd(),'output','outputfile_%s.xlsx' % (time.strftime('%Y%H%M_%S')))


# In[23]:


# 创建一个Pandas Excel writer，使用openpyxl作为引擎  
with pd.ExcelWriter(out_file, engine='openpyxl') as writer:  
    for sheet_name, sheet_data in dict_mml.items():  
        # 将DataFrame写入对应名称的工作表  
        #sheet_data= sheet_data.apply(pd.to_numeric,errors='ignore')
        sheet_data.to_excel(writer, sheet_name=sheet_name, index=False)  


# In[ ]:





# In[25]:


for kk in list(dict_mml.keys()):
    print(kk)

a = input('已转换完成')


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




