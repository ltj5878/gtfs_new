# 票价查询与比价功能 ToDo

## 1. 核心目标
在线路详情页（`/routes/:id`）新增票价信息卡片，展示该线路的成人票价和各乘客类型（Senior/Youth/Child/Disabled 等）的差异化票价对比。不新建独立页面，融入现有 `RouteDetail.vue`。

---

## 2. 现有数据基础

### 数据库表（均已建表且有数据）

| 表名 | 记录数 | 作用 |
|------|--------|------|
| `fare_attributes` | 2,513 | 基础票价（fare_id → price/currency/payment_method/transfers） |
| `fare_rules` | 5,380 | 票价 ↔ 线路关联（fare_id + route_id，origin_id/destination_id 多为空） |
| `rider_categories` | 6 | 乘客类别定义（仅 sf 地区） |
| `fare_rider_categories` | 7,532 | 各乘客类别的差异化票价（fare_id + rider_category_id → price） |

### 实际数据示例

**线路 1（Muni）的票价结构：**
| 身份 | 票价 (USD) |
|------|-----------|
| 成人 (Adult) | $3.00 |
| 老年人 (Senior) | $1.25 |
| 青少年 (Youth) | $0.00 |
| 儿童 (Child) | $0.00 |
| 残障人士 (Disabled) | $1.25 |

**部分线路有多个票价档次**（如线路 12 有 $2.75 和 $3.00 两档），需全部展示。

### 乘客类别（rider_categories，仅 sf 地区）

| rider_category_id | 描述 |
|-------------------|------|
| 2 | Senior |
| 3 | Child |
| 5 | Youth |
| 6 | Disabled |
| 15 | Medicare Cardholder |
| 16 | Clipper START |

### 关键数据关系
```
routes.route_id
    ↓ (fare_rules.route_id)
fare_rules.fare_id
    ↓ (fare_attributes.fare_id)
fare_attributes (成人基准价 price, currency_type, payment_method, transfers)
    ↓ (fare_rider_categories.fare_id)
fare_rider_categories (各类别差异价 rider_category_id → price)
    ↓ (rider_categories.rider_category_id)
rider_categories (类别描述 rider_category_description)
```

### 注意事项
- **origin_id / destination_id 基本为空**：SF 数据中 fare_rules 的起终点字段未填充，票价按线路整体适用，不区分 OD
- **仅 sf 地区有 rider_categories 数据**：nyc 和 sydney 目前无乘客类别票价，需做空数据兜底
- **一条线路可能对应多个 fare_id**（多票价档次），全部需要展示

---

## 3. 后端实现 ToDo

### 3.1 新增 API 路由

- [ ] 在 `backend/api/app.py` 新增 `GET /api/routes/<route_id>/fares`
- [ ] 位置：放在现有 `/api/routes/<route_id>/shapes` 路由附近（约 748 行后）

### 3.2 API 设计

**请求：**
```
GET /api/routes/<route_id>/fares?region=sf
```

**返回 JSON 结构：**
```json
{
  "code": 200,
  "data": {
    "route_id": "1",
    "fares": [
      {
        "fare_id": "415823",
        "price": 3.00,
        "currency_type": "USD",
        "payment_method": 0,
        "transfers": null,
        "transfer_duration": null,
        "rider_categories": [
          { "rider_category_id": "2", "description": "Senior", "price": 1.25 },
          { "rider_category_id": "3", "description": "Child", "price": 0.00 },
          { "rider_category_id": "5", "description": "Youth", "price": 0.00 },
          { "rider_category_id": "6", "description": "Disabled", "price": 1.25 }
        ]
      }
    ]
  }
}
```

### 3.3 SQL 查询逻辑

```sql
-- 第一步：查该线路的所有票价
SELECT DISTINCT fa.fare_id, fa.price, fa.currency_type,
       fa.payment_method, fa.transfers, fa.transfer_duration
FROM fare_attributes fa
JOIN fare_rules fr ON fa.region = fr.region AND fa.fare_id = fr.fare_id
WHERE fr.route_id = %s AND fa.region = %s
ORDER BY fa.price;

-- 第二步：查各票价的乘客类别差异价
SELECT frc.fare_id, frc.rider_category_id,
       rc.rider_category_description, frc.price
FROM fare_rider_categories frc
JOIN rider_categories rc ON frc.region = rc.region
  AND frc.rider_category_id = rc.rider_category_id
WHERE frc.fare_id IN %s AND frc.region = %s
ORDER BY frc.fare_id, frc.price;
```

### 3.4 实现要点
- [ ] region 参数从请求中获取（拦截器自动附加）
- [ ] 无票价数据时返回 `{ "fares": [] }`（不报错）
- [ ] 不需要认证，与其他 routes API 一致
- [ ] payment_method 映射：0 = 上车付费，1 = 提前购票

---

## 4. 前端实现 ToDo

### 4.1 API 层
- [ ] 在 `frontend/src/api/routes.js` 新增：
```js
// 获取线路票价信息
export const getRouteFares = (routeId) => apiClient.get(`/routes/${routeId}/fares`)
```

### 4.2 RouteDetail.vue 修改

**修改文件**：`frontend/src/views/RouteDetail.vue`（当前 487 行）

**插入位置**：在"线路信息" `el-card`（el-descriptions）之后、站点+地图的 `el-row` 之前（约第 66 行 `</el-row>` 之后）

- [ ] template 新增票价卡片：
```html
<!-- 票价信息 -->
<el-row :gutter="20" style="margin-top: 20px;" v-if="fareData && fareData.fares && fareData.fares.length > 0">
  <el-col :xs="24">
    <el-card v-loading="loadingFares">
      <template #header>
        <div class="fare-card-header">
          <span>{{ $t('routeDetail.fareInfo') }}</span>
        </div>
      </template>
      <!-- 遍历每个票价档次 -->
      <div v-for="(fare, idx) in fareData.fares" :key="fare.fare_id" class="fare-block">
        <div v-if="fareData.fares.length > 1" class="fare-block-title">
          票价方案 {{ idx + 1 }}
        </div>
        <!-- 成人票价突出显示 -->
        <div class="fare-adult">
          <span class="fare-adult-label">{{ $t('routeDetail.adultFare') }}</span>
          <span class="fare-adult-price">{{ fare.currency_type === 'USD' ? '$' : fare.currency_type }} {{ fare.price.toFixed(2) }}</span>
        </div>
        <!-- 付款和换乘信息 -->
        <div class="fare-extra">
          <el-tag size="small" type="info">
            {{ fare.payment_method === 0 ? $t('routeDetail.payOnBoard') : $t('routeDetail.payInAdvance') }}
          </el-tag>
          <el-tag v-if="fare.transfers !== null" size="small" type="info">
            {{ fare.transfers === 0 ? $t('routeDetail.noTransfer') : $t('routeDetail.transferCount', { n: fare.transfers }) }}
          </el-tag>
        </div>
        <!-- 各乘客类别比价表格 -->
        <el-table v-if="fare.rider_categories && fare.rider_categories.length" :data="fare.rider_categories" size="small" stripe style="margin-top: 12px;">
          <el-table-column prop="description" :label="$t('routeDetail.riderType')" />
          <el-table-column :label="$t('routeDetail.price')" width="120" align="right">
            <template #default="{ row }">
              <span :class="{ 'fare-free': row.price === 0, 'fare-discount': row.price > 0 && row.price < fare.price }">
                {{ row.price === 0 ? $t('routeDetail.free') : (fare.currency_type === 'USD' ? '$' : fare.currency_type) + ' ' + row.price.toFixed(2) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('routeDetail.discount')" width="100" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.price === 0" type="success" size="small">免费</el-tag>
              <el-tag v-else-if="row.price < fare.price" type="warning" size="small">
                -{{ Math.round((1 - row.price / fare.price) * 100) }}%
              </el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
        </el-table>
        <el-divider v-if="idx < fareData.fares.length - 1" />
      </div>
    </el-card>
  </el-col>
</el-row>
```

- [ ] script setup 新增：
```js
import { getRouteFares } from '@/api/routes.js'

const fareData = ref(null)
const loadingFares = ref(false)

const loadFares = async () => {
  loadingFares.value = true
  try {
    fareData.value = await getRouteFares(route.params.id)
  } catch {
    // 票价不可用不影响页面
  } finally {
    loadingFares.value = false
  }
}
```

- [ ] 在 `onMounted` 中补充调用（与现有逻辑并行，不影响主流程）：
```js
// 在 fetchRouteById 之后
loadFares()  // 独立加载，不 await
```

### 4.3 样式新增
```css
.fare-card-header { display: flex; align-items: center; gap: 8px; }
.fare-block { margin-bottom: 8px; }
.fare-block-title { font-size: 14px; font-weight: 600; color: #606266; margin-bottom: 8px; }
.fare-adult { display: flex; align-items: baseline; gap: 12px; margin-bottom: 8px; }
.fare-adult-label { font-size: 14px; color: #606266; }
.fare-adult-price { font-size: 28px; font-weight: 700; color: #409eff; }
.fare-extra { display: flex; gap: 8px; margin-bottom: 4px; }
.fare-free { color: #67c23a; font-weight: 600; }
.fare-discount { color: #e6a23c; font-weight: 600; }
```

---

## 5. 国际化 ToDo

- [ ] `frontend/src/i18n/zh-CN.js` 在 `routeDetail` 对象中新增：
```js
fareInfo: '票价信息',
adultFare: '成人票价',
payOnBoard: '上车付费',
payInAdvance: '提前购票',
noTransfer: '不可换乘',
transferCount: '可换乘 {n} 次',
riderType: '乘客类型',
price: '票价',
discount: '折扣',
free: '免费',
```

- [ ] `frontend/src/i18n/en.js` 同步新增：
```js
fareInfo: 'Fare Information',
adultFare: 'Adult Fare',
payOnBoard: 'Pay on Board',
payInAdvance: 'Pay in Advance',
noTransfer: 'No Transfer',
transferCount: '{n} Transfer(s)',
riderType: 'Rider Type',
price: 'Price',
discount: 'Discount',
free: 'Free',
```

---

## 6. 文件修改清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/api/app.py` | 新增 | `GET /api/routes/<route_id>/fares` 路由（~40 行） |
| `frontend/src/api/routes.js` | 新增 | `getRouteFares()` 函数（1 行） |
| `frontend/src/views/RouteDetail.vue` | 修改 | 新增票价卡片 template + script 变量/函数 + CSS |
| `frontend/src/i18n/zh-CN.js` | 修改 | routeDetail 下新增 10 个 key |
| `frontend/src/i18n/en.js` | 修改 | routeDetail 下新增 10 个 key |

---

## 7. 不影响现有功能的保障

- 票价卡片用 `v-if="fareData?.fares?.length > 0"` 守卫，无数据时不渲染
- `loadFares()` 独立调用，不 await，失败静默，不阻塞线路详情和地图的加载
- 不修改现有 template 结构，仅在 el-descriptions 卡片和站点+地图行之间插入新 `<el-row>`
- 不修改任何已有的 ref、computed、函数
- nyc/sydney 无 rider_categories 数据时，表格不渲染（fare.rider_categories 为空数组）

---

## 8. 验证方式

```bash
# 确认数据可用
psql gtfs_db -c "SELECT count(*) FROM fare_rules WHERE route_id = '1' AND region = 'sf';"

# 后端测试
curl "http://localhost:5001/api/routes/1/fares?region=sf" | python3 -m json.tool

# 前端验证
# 访问 http://localhost:5173/routes/1 → 线路信息卡片下方应出现票价信息卡片
# 访问 http://localhost:5173/routes/PM → 应看到 $9.00 的票价（Cable Car）
# 访问 nyc 地区线路 → 若无票价，卡片不显示
# 切换深色模式 → 票价卡片样式正常
```
