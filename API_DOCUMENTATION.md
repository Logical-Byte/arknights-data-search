# 明日方舟干员数据查询 API 文档

## 概述
这是一个用于查询《明日方舟》干员数据的简单 API。您可以根据干员的职业、稀有度、位置、词缀等多种条件进行筛选。

## 基础 URL
`http://127.0.0.1:8000`

## 端点: `/api/operators`

### 方法
`GET`

### 描述
获取符合指定筛选条件的干员数据列表。

### 查询参数
所有参数均为可选。

| 参数名          | 类型   | 描述                                     | 可选值                                     |
| :-------------- | :----- | :--------------------------------------- | :----------------------------------------- |
| `name`          | `string` | **姓名**：干员的姓名                     | 任意干员姓名                               |
| `profession`    | `string` | **职业**：干员的职业类型                 | `CASTER`, `MEDIC`, `PIONEER`, `SNIPER`, `SPECIAL`, `SUPPORT`, `TANK`, `TOKEN`, `TRAP`, `WARRIOR` |
| `sub_profession`| `string` | **分支**：干员的子职业分支               | `agent`, `alchemist`, `aoesniper`, `artsfghter`, `artsprotector`, `bard`, `bearer`, `blastcaster`, `blessing`, `bombarder`, `centurion`, `chain`, `chainhealer`, `charger`, `closerange`, `corecaster`, `counsellor`, `craftsman`, `crusher`, `dollkeeper`, `duelist`, `executor`, `fastshot`, `fearless`, `fighter`, `fortress`, `funnel`, `geek`, `guardian`, `hammer`, `healer`, `hookmaster`, `hunter`, `incantationmedic`, `instructor`, `librator`, `longrange`, `loopshooter`, `lord`, `mercenary`, `merchant`, `musha`, `mystic`, `notchar1`, `notchar2`, `phalanx`, `physician`, `pioneer`, `primcaster`, `primguard`, `primprotector`, `protector`, `pusher`, `reaper`, `reaperrange`, `ringhealer`, `ritualist`, `shotprotector`, `siegesniper`, `skybreaker`, `skywalker`, `slower`, `soulcaster`, `splashcaster`, `stalker`, `summoner`, `sword`, `tactician`, `traper`, `underminer`, `unyield`, `wandermedic` |
| `rarity`        | `integer`| **稀有度**：干员的稀有度 (1-6星)         | `1`, `2`, `3`, `4`, `5`, `6` |
| `position`      | `string` | **位置**：干员的部署位置               | `ALL`, `MELEE`, `NONE`, `RANGED` |
| `tag`           | `string` | **词缀**：干员的标签                     | `位移`, `元素`, `减速`, `削弱`, `召唤`, `快速复活`, `控场`, `支援`, `支援机械`, `新手`, `治疗`, `爆发`, `生存`, `群攻`, `费用回复`, `输出`, `防护`, `高空` |
| `nation`        | `string` | **势力**：干员所属的势力                 | `bolivar`, `columbia`, `egir`, `higashi`, `iberia`, `kazimierz`, `kjerag`, `laterano`, `leithanien`, `lungmen`, `minos`, `rhodes`, `rim`, `sami`, `sargon`, `siracusa`, `ursus`, `victoria`, `yan` |
| `gender`        | `string` | **性别**：干员的性别                     | `女`, `女士`, `断罪`, `未知`, `男` |
| `birth_place`   | `string` | **出身地**：干员的出身地                 | `不明`, `雷姆必拓`, `东国`, `东方大陆（自称）`, `乌萨斯`, `伊兹甘达（自称）`, `伊比利亚`, `北方大陆（自称）`, `卡兹戴尔`, `卡西米尔`, `叙拉古`, `哥伦比亚`, `因经纪公司要求不公开`, `拉特兰`, `未公开`, `未知`, `杜林`, `汐斯塔`, `汐斯塔（独立城邦）`, `炎`, `玻利瓦尔`, `瓦伊凡`, `米诺斯`, `维多利亚`, `罗德岛`, `莱塔尼亚`, `萨尔贡`, `萨米`, `谢拉格`, `阿戈尔`, `阿戈尔地区`, `雷姆必拓`, `龙门` |
| `race`          | `string` | **种族**：干员的种族                     | `卡特斯`, `不明`, `丰蹄`, `乌萨斯`, `佩洛`, `伊特拉`, `匹特拉姆`, `半身人（自称）`, `卡普里尼`, `卡特斯/奇美拉`, `因经纪公司要求不公开`, `埃拉菲亚`, `塞拉托`, `安努拉`, `库兰塔`, `德拉克`, `斯库缇`, `曼提科`, `未公开`, `未知`, `未知（疑似黎博利）`, `札拉克`, `杜林`, `沃尔珀`, `萨弗拉`, `瓦伊凡`, `皮洛萨`, `矮人（自称）`, `精灵`, `菲林`, `萨卡兹`, `萨弗拉`, `萨科塔`, `长身人（自称）`, `阿戈尔`, `阿斯兰`, `阿纳缇`, `阿纳萨`, `阿达克利斯`, `鬼`, `鲁珀`, `麒麟`, `黎博利`, `龙` |
| `obtain_approach`| `string` | **获取途径**：干员的获取方式             | `主题曲剧情`, `信用交易所`, `凭证交易所`, `周年奖励`, `招募寻访`, `招募寻访/见习任务`, `活动获得`, `限时礼包`, `集成战略获得` |

### 示例用法

**1. 获取所有干员**
```bash
curl http://127.0.0.1:8000/api/operators
```

**2. 查询稀有度为 6 的干员**
```bash
curl "http://127.0.0.1:8000/api/operators?rarity=6"
```

**3. 查询职业为“狙击”、性别为“女”的干员**
```bash
curl "http://127.0.0.1:8000/api/operators?profession=SNIPER&gender=女"
```

**4. 查询出身地为“东国”、种族为“鬼”的干员**
```bash
curl "http://127.0.0.1:8000/api/operators?birth_place=东国&race=鬼"
```

**5. 查询包含“支援机械”词缀的干员**
```bash
curl "http://127.0.0.1:8000/api/operators?tag=支援机械"
```

### 示例响应
成功请求将返回一个 JSON 数组，其中包含符合条件的干员对象。每个干员对象包含以下字段：

```json
[
  {
    "charId": "char_002_amiya",
    "name": "阿米娅",
    "description": "罗德岛的公开领袖，在多次行动中积极活跃。在战场上她是指挥官，是值得信赖的伙伴，在生活中她也同我们一样，是个不折不扣的普通女孩。 但那双纤细的双手，却早已肩负了远超常人的重担。 ",
    "canUseGeneralPotentialItem": true,
    "potentialItemId": "p_char_002_amiya",
    "nationId": "rhodes",
    "groupId": null,
    "teamId": null,
    "displayNumber": "RC01",
    "appellation": "阿米娅",
    "position": "RANGED",
    "tagList": [
      "近卫",
      "术师",
      "核心"
    ],
    "itemUsage": "罗德岛的公开领袖，在多次行动中积极活跃。",
    "itemDesc": "她那双纤细的双手，却早已肩负了远超常人的重担。",
    "itemObtainApproach": "完成新手教程",
    "isNotObtainable": false,
    "isSpChar": false,
    "maxPotentialLevel": 5,
    "rarity": "TIER_5",
    "profession": "CASTER",
    "subProfessionId": "aoe",
    "gender": "女",
    "birth_place": "未知",
    "race": "奇美拉"
  },
  {
    "charId": "char_500_noirc",
    "name": "Lancet-2",
    "description": "恢复友方单位生命，且不受部署数量限制，但再部署时间极长",
    "canUseGeneralPotentialItem": false,
    "potentialItemId": "p_char_285_medic2",
    "nationId": "rhodes",
    "groupId": null,
    "teamId": null,
    "displayNumber": "RCX2",
    "appellation": "Lancet-2",
    "position": "RANGED",
    "tagList": [
      "支援机械",
      "治疗"
    ],
    "itemUsage": "罗德岛医疗机器人Lancet-2，被工程师可露希尔派遣来执行战地医疗任务。",
    "itemDesc": "她知道自己是一台机器人。",
    "itemObtainApproach": "招募寻访",
    "isNotObtainable": false,
    "isSpChar": false,
    "maxPotentialLevel": 5,
    "rarity": "TIER_1",
    "profession": "MEDIC",
    "subProfessionId": "physician",
    "gender": "男",
    "birth_place": "东国",
    "race": "鬼"
  }
]
```
