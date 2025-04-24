#Resource Group
$resourceGroup = "TestGroup"
$location = "westus"

#VirtualNet
$vNet = "TestVnet"
$subnet = "testSubNet1"
$addressPrefix = "10.0.0.0/16"
$subnetPrefix = "10.0.0.0/24"

New-AzResourceGroup -Name $resourceGroup -Location $location

$subnetConfig = New-AzVirtualNetworkSubnetConfig -Name $subnet -AddressPrefix $subnetPrefix

New-AzVirtualNetwork -Name $vnetName `
    -ResourceGroupName $resourceGroup `
    -Location $location `
    -AddressPrefix $addressPrefix `
    -Subnet $subnetConfig

