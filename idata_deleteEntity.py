#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Author: Wlka
Date: 2019-5-1
Description:
    iData二次开发python竞赛程序源文件
    测试文件为官方提供的study.mdb以及手动创建的一些测试用例
    处理5000个实体平均用时9s
Implementation:
    程序先检测是否打开了文档，然后按图层获取实体列表，接着获取指定的实体属性组成列表，比较列表内重复部分，进行去重操作，
    去重后，将剩余的属性列表进行逐个比较，找到重复度较高的部分，进行高亮显示，然后让用户自行选择是否删除

"""

import PyiData as pid


def main():
    """
    主函数
    """
    layers = getLayers()
    dedupListList = deleteRepeatEntitys(layers)
    deleteSimilarEntity(layers, dedupListList)


def getLayers():
    """
    获取当前数据库的所有图层

    Parameters
    ----------
    None

    Returns
    -------
    layers: list
        返回一个包含所有图层的列表
    """
    if not pid.isDocumentActived():
        print("文档未打开")
        pid.iDataPrintf("文档未打开")
        return

    layers = pid.iDataGetLayerList()  # 获取图层列表
    return layers


def getEntityAttr(entity):
    """
    获取实体的所有属性
    Parameters
    ----------
    entity: PyiData.iDataEntity
        传入参数为实体

    Returns
    -------
    attrDict: dict
        返回一个包含实体所有属性信息的字典
    """
    testList = []  # 存储属性的列表

    testList.append(entity.getCode())
    testList.append(entity.getName())
    testList.append(str(entity.pos()))
    testList.append(entity.getArea())
    testList.append(entity.getLength())
    testList.append(entity.getNodesSize())
    testList.append(str(entity.getParts()))
    testList.append(entity.getHeight())
    testList.append(entity.rotation())
    testList.append(entity.isCurveFit())
    testList.append(entity.isBulges())
    testList.append(entity.userCode())
    testList.append(entity.getGroupID())
    testList.append(entity.isHasText())
    testList.append(str(entity.getColor()))
    testList.append(entity.getColorIndex())
    testList.append(entity.getWidth())
    testList.append(entity.isMask())
    testList.append(str(entity.Dirty()))
    testList.append(entity.getmd5())
    testList.append(entity.isOK())
    testList.append(str(entity.getCurSelIdx()))
    testList.append(entity.getOrder())
    testList.append(str(entity.getBoundingRect()))
    testList.append(entity.entStatus())
    testList.append(entity.entlStatus())
    testList.append(entity.getNodesBinMD5())
    testList.append(str(entity.property()))

    # 获取节点信息
    for ls in entity.getNodes()[0]:
        for i in ls:
            testList.append(str(i))
    for ls in entity.getNodes()[1]:
        for i in ls:
            testList.append(str(i))

    # 获取扩展属性
    propertyMap = entity.getXDataAll()
    for k, v in propertyMap.iteritems():
        if type(v) == pid.Variant:
            v = v.toString()
        if k != "GLOBALID":  # 属性列表是为了去重，所以不需要全局ID
            testList.append(v)
    return testList


def deleteRepeatEntitys(layers):
    """
    删除当前数据库中的重复实体
    Parameters
    ----------
    layers: list
        传入参数为图层列表

    Returns
    -------
    dedupListList: listlist
        传出参数为去重后的属性列表，每个图层的全部实体的属性组合成一个子列表
    """

    pid.iDataCreateProgress("删除重复实体中")  # 设置进度条提示
    progressCurValue = 0    #进度条数值

    deleteEntityList = []  # 存储重复实体的列表，后面统一删除
    dedupListList = []
    for layer in layers:
        pid.iDataSetProgressValue(progressCurValue, totalStep=len(layers))  # 按每遍历一个图层，进度条数值加1
        progressCurValue += 1
        e, entityList = pid.iDataSSGetX(layer.getName())  # 获得同一图层且同编码的所有实体
        if e == pid.iData.eOk and len(entityList):
            attrList = []
            for entity in entityList:
                attrList.append(getEntityAttr(entity))  # 获取到实体的属性列表，并添加到attrList中，便于后续操作

            dedupList = [list(t) for t in set(tuple(_) for _ in attrList)]  # 获得去重后的实体属性列表
            dedupList.sort(key=attrList.index)  # 保持原列表中的顺序

            # 返回去重后的实体属性列表，用于后续删除被修过的实体
            dedupListList.append(dedupList)

            # 比较去重后的列表和原始列表，获取要被删除数据的索引
            deletePosition = []
            i, j = 0, 0
            while i < len(attrList) and j < len(dedupList):
                if attrList[i] == dedupList[j]:
                    i += 1
                    j += 1
                    continue
                else:
                    deletePosition.append(i)
                    i += 1
            if i < len(attrList) and j == len(dedupList):
                for num in range(i, len(attrList)):
                    deletePosition.append(num)

            # 遍历同一图层上所有的实体，并删除重复的实体
            if len(deletePosition):
                cnt = -1
                for entity in entityList:
                    cnt += 1
                    if cnt in deletePosition:
                        deleteEntityList.append(entity)
                        pid.iDataDeleteEntity(entity)  # 删除图面实体

    pid.CommitEntity(deleteEntityList, pid.iData.kErased)  # 删除数据库里的对应实体
    pid.iDataRegen(None, True)  # 刷新图面

    pid.iDataCloseProgress()  # 关闭进度条

    return dedupListList


def deleteSimilarEntity(layers, dedupListList):
    """
    删除当前数据库中的部分重复实体
    Parameters
    ----------
    layers: list
        传入参数为图层列表
    dedupListList:listlist
        传入参数为去重后的属性列表，每个图层的全部实体的属性组合成一个子列表

    Returns
    -------
    None
    """

    pid.iDataCreateProgress("删除属性重复实体")  # 设置进度条提示
    progressCurValue = 0    #进度条数值

    indexListList = []  # 将符合条件的实体索引添加进列表，按图层将列表组合成一个新列表
    for dedupList in dedupListList:
        indexList = []  # 将符合条件的实体索引添加进列表
        flagList = []  # 避免重复遍历
        for i in range(len(dedupList)):
            if i in flagList:  # 当i属于flagList的部分，跳过循环
                continue
            tmpList = []  # 一个存储索引的临时列表
            for j in range(i + 1, len(dedupList)):
                sameAttrCount = 0  # 记录两个实体的重复属性数量
                if len(dedupList[i]) != len(dedupList[j]):
                    continue
                for k in range(len(dedupList[i])):
                    if dedupList[i][k] == dedupList[j][k]:
                        sameAttrCount += 1
                if sameAttrCount >= len(dedupList[i]) * 0.5:  # 当两个实体重复实体数量超过一半时将索引添加进临时列表以及flagList
                    tmpList.append(j)
                    flagList.append(j)
            if len(tmpList):  # 当临时列表不为空时，将i插入当临时列表前面，并添加进indexList
                tmpList.insert(0, i)
                indexList.append(tmpList)
        indexListList.append(indexList)

    cnt = 0  # 遍历操作计数器
    deleteEntityList = []  # 将待删除的实体存储起来，最后一并删除
    for layer in layers:  # 按图层遍历
        pid.iDataSetProgressValue(progressCurValue, totalStep=len(layers))  # 按每遍历一个图层，进度条数值加1
        progressCurValue += 1

        e, entityList = pid.iDataSSGetX(layer.getName())  # 获得同一图层且同编码的所有实体
        if e == pid.iData.eOk and len(entityList):
            if len(indexListList[cnt]) == 0:  # 当部分重复实体列表为空时，跳过此次操作
                cnt += 1
                continue
            highLightList = []
            for entityIndex in range(len(entityList)):
                if entityIndex in indexListList[cnt][0]:
                    entityList[entityIndex].setHighLight(True)
                    highLightList.append(entityList[entityIndex])
            while len(highLightList):
                e, entity, point = pid.iDataEntSel("请选择要删除的实体")
                if e == pid.iData.eCancel:
                    cnt += 1
                    pid.clearHighLight()
                    break
                while entity not in highLightList:
                    e, entity, point = pid.iDataEntSel("请选择高亮部分的实体")
                    if e == pid.iData.eCancel:
                        cnt += 1
                        pid.clearHighLight()
                        break
                pid.iDataDeleteEntity(entity)
                highLightList.remove(entity)
                deleteEntityList.append(entity)

    pid.CommitEntity(deleteEntityList, pid.iData.kErased)  # 删除数据库里的对应实体
    pid.iDataRegen(None, True)  # 刷新图面

    pid.iDataCloseProgress()  # 关闭进度条

if __name__ == "__main__":
    main()
