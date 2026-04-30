# MI Kusto Tables Reference
Generated from schema queries against `sqlazure1` on `https://sqlazureeas2follower.eastasia.kusto.windows.net`.
Last updated: 2026-04-29

---

## Common Columns

The following columns appear across many MI monitoring tables and are intentionally documented once:

| Column | Type | Description |
|--------|------|-------------|
| TIMESTAMP | datetime | Ingestion timestamp used for time-range filters. |
| PreciseTimeStamp | datetime | Precise event timestamp from the source component. |
| ClusterName | string | Cluster or ring name hosting the MI workload. |
| NodeRole | string | Node role within the service or cluster. |
| MachineName | string | Underlying machine name. |
| NodeName | string | Node identifier inside the cluster. |
| AppName | string | Application or package instance name. |
| AppTypeName | string | Application type; use `startswith("Worker.CL")` to scope to MI workloads. |
| LogicalServerName | string | Managed Instance server name; primary MI filter in many tables. |
| SubscriptionId | string | Azure subscription identifier associated with the MI resource. |
| ResourceGroup | string | Azure resource group associated with the MI resource. |

---

# 1. Instance & Database Metadata

## MonAnalyticsDBSnapshot — Database analytics and snapshot metadata

**Purpose**: Database analytics and snapshot metadata. Used to identify configuration, inventory, and latest known state for MI instances, databases, and related platform objects. Referenced in MI template areas: availability, backup-restore, general, performance. Often used during backup or restore investigations.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| active_backup_storage_type | string | Type classification for active backup storage. |
| analytics_service_type | string | Type classification for analytics service. |
| archived_backup_container_certificate_expiration_date | datetime | Archived backup container certificate expiration date. |
| archived_backup_container_id | string | Archived backup container identifier. |
| archived_backup_enabled | long | Archived backup enabled. |
| archived_backup_retention_policy_name | string | Archived backup retention policy name. |
| archived_backup_vault_name | string | Archived backup vault name. |
| archived_backup_vault_resource_group | string | Archived backup vault resource group. |
| backup_retention_days | long | Backup retention days. |
| code_package_version | string | Code package version. |
| containment_state | long | State value for containment. |
| create_mode | string | Create mode. |
| create_time | datetime | Creation timestamp. |
| customer_subscription_id | string | Customer subscription identifier. |
| database_level_encryption_protector | string | Database level encryption protector. |
| database_type | string | Type classification for database. |
| database_usage_status | string | Status value for database usage. |
| deactivated_last_known_data_file_size_mb | long | Deactivated last known data file size mb. |
| deactivated_last_known_database_size_mb | long | Deactivated last known database size mb. |
| deactivated_last_known_encryption_operation_percentage | real | Deactivated last known encryption operation pe percentage. |
| deactivated_last_known_encryption_operation_state | long | State value for deactivated last known encryption operation. |
| deactivated_last_known_encryption_operation_valid | long | Deactivated last known encryption operation valid. |
| deactivated_last_known_log_file_size_mb | long | Deactivated last known log file size mb. |
| edition | string | Edition. |
| enclave_type | string | Type classification for enclave. |
| encryption | long | Encryption. |
| encryption_protector_auto_rotation | long | Encryption protector auto rotation. |
| end_utc_date | datetime | End utc date. |
| fabric_application_uri | string | Fabric application uri. |
| fabric_partition_id | string | Fabric partition identifier. |
| fabric_service_type_name | string | Fabric service type name. |
| fabric_service_uri | string | Fabric service uri. |
| failover_group_id | string | Failover group identifier. |
| federated_client_id_configured | long | Federated client id configured. |
| file_share_name | string | File share name. |
| first_backup_time | datetime | First backup time timestamp. |
| free_limit_exhaustion_behavior | string | Free limit exhaustion behavior. |
| identity_type | string | Type classification for identity. |
| is_billable_database | long | Boolean flag indicating whether billable database. |
| is_migration_source_cluster_sawav1 | long | Boolean flag indicating whether migration source cluster sawav1. |
| last_update_time | datetime | Last update time timestamp. |
| license_type | string | Type classification for license. |
| logical_availability_zone | string | Logical availability zone. |
| logical_database_id | string | Logical database identifier. |
| logical_database_name | string | Logical database name. |
| logical_resource_pool_id | string | Logical resource pool identifier. |
| logical_server_id | string | Logical server identifier. |
| maint_config_internal_id | string | Maint config internal identifier. |
| max_migration_low_key | long | Maximum migration low key. |
| max_size_bytes | long | Max size size in bytes. |
| migration_end_time | datetime | Migration end time timestamp. |
| migration_source_cluster | string | Migration source cluster. |
| migration_start_time | datetime | Migration start time timestamp. |
| pending_full_backup_bsr_type | string | Type classification for pending full backup bsr. |
| physical_compute_state | string | State value for physical compute. |
| physical_database_id | string | Physical database identifier. |
| physical_database_state | string | State value for physical database. |
| pitr_immutability_extended | long | Pitr immutability extended. |
| read_scale_units | long | Read scale units. |
| region_name | string | Region name. |
| requested_backup_storage_type | string | Type classification for requested backup storage. |
| rg_databasesettings_config_version | long | Resource governor databasesettings config version. |
| rg_slopropertybag_config_version | long | Resource governor slopropertybag config version. |
| server_dtu_quota | long | Server dtu quota. |
| service_level_objective | string | Service level objective. |
| sl_auto_pause_delay | long | Sl auto pause delay. |
| sl_min_capacity | real | Sl min capacity. |
| sql_database_id | long | SQL database identifier. |
| sql_instance_name | string | SQL instance name. |
| start_utc_date | datetime | Start utc date. |
| state | string | Current lifecycle or health state. |
| storage_account_name | string | Storage account name. |
| tenant_ring_name | string | Tenant ring name. |
| tenant_ring_placement_metadata | string | Tenant ring placement metadata. |
| trident_artifact_id | string | Trident artifact identifier. |
| trident_capacity_id | string | Trident capacity identifier. |
| trident_workspace_id | string | Trident workspace identifier. |
| use_free_limit | long | Use free limit. |
| vldb_xlog_coordinator_id | string | Vldb xlog coordinator identifier. |
| whitelist_expiration_time_for_current_storage_account | datetime | Whitelist expiration time for current storage account. |
| xtp_enabled | long | In-Memory OLTP enabled. |
| zone_resilient | long | Zone resilient. |

## MonCapacityTenantSnapshot — Tenant ring and capacity snapshot

**Purpose**: Tenant ring and capacity snapshot. Used to identify configuration, inventory, and latest known state for MI instances, databases, and related platform objects. Referenced in MI template areas: networking.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| allowed_service_level_objectives | string | Allowed service level objectives. |
| application_placement_label | string | Application placement label. |
| availability_zone_mapping | string | Availability zone mapping. |
| buffer_protection_weight | long | Buffer protection weight. |
| capacity_reservation_on | long | Capacity reservation on. |
| capacity_tag | string | Capacity tag. |
| code_package_version | string | Code package version. |
| config_type | string | Type classification for config. |
| connectivity_last_error_at | datetime | Connectivity last error at. |
| connectivity_last_healthy_at | datetime | Connectivity last healthy at. |
| connectivity_succeeded | long | Connectivity succeeded. |
| create_time | datetime | Creation timestamp. |
| current_cpu_capacity | long | Current CPU capacity. |
| custom_maintenance_settings_xml | string | Custom maintenance settings xml. |
| customer_subscription_id | string | Customer subscription identifier. |
| effective_overbooking_ratio_percentage | long | Effective overbooking ratio pe percentage. |
| end_utc_date | datetime | End utc date. |
| fabric_controller_name | string | Fabric controller name. |
| fault_domain_count | long | Number of fault domain. |
| fsm_extension_data | string | Fsm extension data. |
| hosted_service_name | string | Hosted service name. |
| hosted_service_subscription_id | string | Hosted service subscription identifier. |
| image_store_connectivity_last_error_at | datetime | Image store connectivity last error at. |
| image_store_connectivity_last_healthy_at | datetime | Image store connectivity last healthy at. |
| image_store_connectivity_succeeded | long | Image store connectivity succeeded. |
| is_ipv6_enabled | long | Boolean flag indicating whether ipv6 enabled. |
| is_paas_v2 | long | Boolean flag indicating whether paas v2. |
| is_paas_v2_multi_az | long | Boolean flag indicating whether paas v2 multi az. |
| last_replica_count_update_time | datetime | Last replica count update time timestamp. |
| maintenance_schedule_id | string | Maintenance schedule identifier. |
| node_count | long | Number of node. |
| overbooking_ratio_percentage | long | Overbooking ratio pe percentage. |
| overbooking_serverless_sellable_ratio_percentage | long | Overbooking serverless sellable ratio pe percentage. |
| per_metric_percentage_cap_overrides | string | Per metric percentage cap overrides. |
| percentage_cap | long | Percentage cap. |
| physical_zone | string | Physical zone. |
| placement_affinity_tag | string | Placement affinity tag. |
| placement_base_weight | long | Placement base weight. |
| placement_last_change_date | datetime | Placement last change date. |
| placement_preference_tag | string | Placement preference tag. |
| placement_preference_tag_isolation_flag | long | Placement preference tag isolation flag. |
| private_cluster_id | string | Private cluster identifier. |
| replica_count | long | Number of replica. |
| replica_count_limit_override | long | Replica count limit override. |
| sellable_ratio_percentage | long | Sellable ratio pe percentage. |
| start_utc_date | datetime | Start utc date. |
| state | string | Current lifecycle or health state. |
| tenant_name | string | Tenant name. |
| tenant_ring_name | string | Tenant ring name. |
| tenant_ring_properties_xml | string | Tenant ring properties xml. |
| total_cpu_capacity | long | Total CPU capacity. |
| unit_cpu_capacity | long | Unit CPU capacity. |
| upgrade_domain_count | long | Number of upgrade domain. |
| used_cpu_capacity | long | Used CPU capacity. |
| used_cpu_capacity_dsmcu | long | Used CPU capacity dsmcu. |
| used_cpu_capacity_smcu | long | Used CPU capacity smcu. |
| vm_size | string | Vm size. |
| zone_pinned_capacities | string | Zone pinned capacities. |

## MonDatabaseEncryptionKeys — Database Encryption Keys

**Purpose**: Database Encryption Keys. Used to identify configuration, inventory, and latest known state for MI instances, databases, and related platform objects. Referenced in MI template areas: backup-restore. Often used during backup or restore investigations.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| code_package_version | string | Code package version. |
| create_date | datetime | Create date. |
| database_id | long | Database identifier. |
| encryption_scan_state | long | State value for encryption scan. |
| encryption_state | long | State value for encryption. |
| encryptor_thumbprint | string | Encryptor thumbprint. |
| encryptor_type | string | Type classification for encryptor. |
| end_utc_date | datetime | End utc date. |
| is_encrypted | long | Boolean flag indicating whether encrypted. |
| is_primary_replica | long | Boolean flag indicating whether primary replica. |
| key_algorithm | string | Key algorithm. |
| key_length | long | Key length. |
| logical_database_id | string | Logical database identifier. |
| modify_date | datetime | Modify date. |
| name | string | Object or resource name. |
| opened_date | datetime | Opened date. |
| percent_complete | float | Percent complete. |
| regenerate_date | datetime | Regenerate date. |
| set_date | datetime | Set date. |
| start_utc_date | datetime | Start utc date. |

## MonDatabaseMetadata — Database Metadata

**Purpose**: Database Metadata. Used to identify configuration, inventory, and latest known state for MI instances, databases, and related platform objects. Referenced in MI template areas: availability, backup-restore, general, performance. Often used during backup or restore investigations.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| algorithm | string | Algorithm. |
| audit_spec_id | long | Audit spec identifier. |
| auid | long | Auid. |
| bXVTDocidUseBaseT | long | B XVTDocid Use Base T. |
| batchsize | long | Batchsize. |
| bitlength | long | Bitlength. |
| bitpos | long | Bitpos. |
| brickid | long | Brickid. |
| catalog | string | Catalog. |
| category | long | Category. |
| chk | long | Chk. |
| cid | long | Cid. |
| class | long | Class. |
| closed_time | datetime | Closed time timestamp. |
| cmprlevel | long | Cmprlevel. |
| cmptlevel | long | Cmptlevel. |
| code_package_version | string | Code package version. |
| colid | long | Colid. |
| collationid | long | Collationid. |
| column_id | long | Column identifier. |
| compid | long | Compid. |
| compressed_reason | long | Compressed reason. |
| connecttimeout | long | Connecttimeout. |
| container_id | long | Container identifier. |
| contract | long | Contract. |
| convgroup | string | Convgroup. |
| crdate | datetime | Crdate. |
| created | datetime | Created. |
| created_time | datetime | Created time timestamp. |
| credential_id | long | Credential identifier. |
| crend | datetime | Crend. |
| crerrors | long | Crerrors. |
| crrows | long | Crrows. |
| crstart | datetime | Crstart. |
| crtype | string | Crtype. |
| data_compression | string | Data compression. |
| data_source_id | long | Data source identifier. |
| dataspace | long | Dataspace. |
| date_format | string | Date format. |
| dbid | long | Dbid. |
| dbname | string | Dbname. |
| deflanguage | string | Deflanguage. |
| depclass | long | Depclass. |
| depid | long | Depid. |
| depsubid | long | Depsubid. |
| dflt | string | Dflt. |
| dfltsch | string | Dfltsch. |
| diagid | string | Diagid. |
| dictionary_id | long | Dictionary identifier. |
| diffbaseguid | string | Diffbaseguid. |
| diffbasetime | datetime | Diffbasetime. |
| dlgerr | long | Dlgerr. |
| dlgid | string | Dlgid. |
| dlgopened | datetime | Dlgopened. |
| dlgtimer | datetime | Dlgtimer. |
| ds_hobtid | long | Ds hobtid. |
| encoding | string | Encoding. |
| encrtype | string | Encrtype. |
| enddlgseq | long | Enddlgseq. |
| enqtime | datetime | Enqtime. |
| entry_count | long | Number of entry. |
| externaloid | string | Externaloid. |
| extractor | string | Extractor. |
| farbrkrinst | string | Farbrkrinst. |
| farprincid | long | Farprincid. |
| farsvc | string | Farsvc. |
| fgid | long | Fgid. |
| fgidfs | long | Fgidfs. |
| field_terminator | string | Field terminator. |
| file_format_id | long | File format identifier. |
| fileguid | string | Fileguid. |
| fileid | long | Fileid. |
| filestate | long | Filestate. |
| filetype | long | Filetype. |
| fillfact | long | Fillfact. |
| finitiator | long | Finitiator. |
| first_row | long | First row. |
| firstoorder | long | Firstoorder. |
| flags | long | Flags. |
| forkguid | string | Forkguid. |
| forkvc | long | Forkvc. |
| format_type | string | Type classification for format. |
| fragid | long | Fragid. |
| frombrkrinst | string | Frombrkrinst. |
| fromsvc | string | Fromsvc. |
| generation | long | Generation. |
| grantee | long | Grantee. |
| grantor | long | Grantor. |
| growth | long | Growth. |
| grpid | long | Grpid. |
| guid | string | Guid. |
| handle | string | Handle. |
| hbcolid | long | Hbcolid. |
| hdrpartlen | long | Hdrpartlen. |
| hdrseclen | long | Hdrseclen. |
| hobt_id | long | Hobt identifier. |
| id | long | identifier. |
| idmajor | long | Idmajor. |
| idminor | long | Idminor. |
| indepclass | long | Indepclass. |
| indepdb | string | Indepdb. |
| indepid | long | Indepid. |
| indepname | string | Indepname. |
| indepschema | string | Indepschema. |
| indepserver | string | Indepserver. |
| indepsubid | long | Indepsubid. |
| indexid | long | Indexid. |
| indid | long | Indid. |
| initiator | long | Initiator. |
| inseskeyid | string | Inseskeyid. |
| internalstatus | long | Internalstatus. |
| intprop | long | Intprop. |
| lang | string | Lang. |
| last_id | long | Last identifier. |
| lastoorder | long | Lastoorder. |
| lastoorderfr | long | Lastoorderfr. |
| lastpkeybackup | datetime | Lastpkeybackup. |
| lcid | long | Lcid. |
| length | long | Length. |
| lgnid | long | Lgnid. |
| lifetime | datetime | Lifetime. |
| lname | string | Lname. |
| lobds | long | Lobds. |
| location | string | Location. |
| logical_database_guid | string | Logical database guid. |
| logical_db_name | string | Logical database name. |
| maxinrow | long | Maxinrow. |
| maxinrowlen | long | Maxinrowlen. |
| maxint | long | Maxint. |
| maxleaf | long | Maxleaf. |
| maxnullbit | long | Maxnullbit. |
| maxsize | long | Maxsize. |
| metadata_offset | long | Metadata offset. |
| metadata_size | long | Metadata size. |
| minint | long | Minint. |
| minleaf | long | Minleaf. |
| modate | datetime | Modate. |
| modified | datetime | Modified. |
| msgbodylen | long | Msgbodylen. |
| msgenc | long | Msgenc. |
| msgid | string | Msgid. |
| msgref | long | Msgref. |
| msgseqnum | long | Msgseqnum. |
| msgtype | string | Msgtype. |
| name | string | Object or resource name. |
| nextdocid | long | Nextdocid. |
| nsclass | long | Nsclass. |
| nsid | long | Nsid. |
| nullbit | long | Nullbit. |
| number | long | Number. |
| numpart | long | Numpart. |
| object_id | long | Object identifier. |
| objid | long | Objid. |
| offset | long | Offset. |
| on_disk_size | long | On disk size. |
| ordkey | long | Ordkey. |
| ordlock | long | Ordlock. |
| outseskeyid | string | Outseskeyid. |
| ownerid | long | Ownerid. |
| ownertype | long | Ownertype. |
| parser_version | string | Parser version. |
| pcdata | long | Pcdata. |
| pclass | long | Pclass. |
| pcreserved | long | Pcreserved. |
| pcused | long | Pcused. |
| phfgid | long | Phfgid. |
| physical_database_guid | string | Physical database guid. |
| physical_db_name | string | Physical database name. |
| pid | long | Pid. |
| placingid | long | Placingid. |
| pname | string | Pname. |
| prec | long | Prec. |
| princid | long | Princid. |
| priority | long | Priority. |
| product | string | Product. |
| provider | string | Provider. |
| pruid | long | Pruid. |
| pushdown | string | Pushdown. |
| pwdset | datetime | Pwdset. |
| qid | long | Qid. |
| querytimeout | long | Querytimeout. |
| rcmodified | long | Rcmodified. |
| rcrows | long | Rcrows. |
| rcvfrag | long | Rcvfrag. |
| rcvseq | long | Rcvseq. |
| redostartforkguid | string | Redostartforkguid. |
| refcount | long | Refcount. |
| reject_sample_value | real | Reject sample value. |
| reject_type | string | Type classification for reject. |
| reject_value | real | Reject value. |
| row_count | long | Number of row. |
| row_terminator | string | Row terminator. |
| rowset | long | Rowset. |
| rowsetid | long | Rowsetid. |
| rowsetnum | long | Rowsetnum. |
| rscolid | long | Rscolid. |
| rsid | long | Rsid. |
| rsndtime | datetime | Rsndtime. |
| scale | long | Scale. |
| schid | long | Schid. |
| scope | long | Scope. |
| scope_id | long | Scope identifier. |
| segment_id | long | Segment identifier. |
| sendseq | long | Sendseq. |
| sensitivity | long | Sensitivity. |
| serde_method | string | Serde method. |
| service_id | long | Service identifier. |
| shard_map_manager_db | string | Shard map manager database. |
| shard_map_name | string | Shard map name. |
| sharding_col_id | long | Sharding col identifier. |
| sharding_dist_type | long | Type classification for sharding dist. |
| size | long | Size. |
| source_schema_name | string | Source schema name. |
| source_table_name | string | Source table name. |
| srvid | long | Srvid. |
| state | string | Current lifecycle or health state. |
| status | long | Current status reported by the component. |
| status2 | long | Status2. |
| stoplistid | long | Stoplistid. |
| string_delimiter | string | String delimiter. |
| subid | long | Subid. |
| subobjid | long | Subobjid. |
| svcbrkrguid | string | Svcbrkrguid. |
| svccontr | string | Svccontr. |
| svcid | long | Svcid. |
| sysseq | long | Sysseq. |
| table_name | string | Table name. |
| tenantid | string | Tenantid. |
| thumbprint | string | Thumbprint. |
| ti | long | Ti. |
| tinyprop | long | Tinyprop. |
| tinyprop1 | long | Tinyprop1. |
| tinyprop2 | long | Tinyprop2. |
| tinyprop3 | long | Tinyprop3. |
| tinyprop4 | long | Tinyprop4. |
| tobrkrinst | string | Tobrkrinst. |
| tosvc | string | Tosvc. |
| type | string | Type. |
| type_desc | string | Type desc. |
| unackmfn | long | Unackmfn. |
| use_type_default | long | Use type default. |
| utype | long | Utype. |
| valclass | long | Valclass. |
| valnum | long | Valnum. |
| value | string | Value. |
| version | long | Version. |
| xmlns | long | Xmlns. |
| xtype | long | Xtype. |

## MonManagedDatabases — Managed database inventory and state snapshot

**Purpose**: Managed database inventory and state snapshot. Used to identify configuration, inventory, and latest known state for MI instances, databases, and related platform objects. Referenced in MI template areas: backup-restore, general. Often used for sizing or billing-related investigations. Often used during backup or restore investigations.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| backup_retention_days | long | Backup retention days. |
| backup_windows_config | string | Backup windows config. |
| code_package_version | string | Code package version. |
| collation | string | Collation. |
| concurrency_token | long | Concurrency token. |
| create_mode | string | Create mode. |
| create_time | datetime | Creation timestamp. |
| created_time | datetime | Created time timestamp. |
| database_type | string | Type classification for database. |
| dropped_time | datetime | Dropped time timestamp. |
| end_utc_date | datetime | End utc date. |
| failover_group_id | string | Failover group identifier. |
| first_backup_time | datetime | First backup time timestamp. |
| fsm_context_instance_name | string | Fsm context instance name. |
| fsm_extension_data | string | Fsm extension data. |
| fsm_instance_id | string | Fsm instance identifier. |
| fsm_timer_event_version | long | Fsm timer event version. |
| fsm_version | long | Fsm version. |
| hekaton_file_group_id | long | Hekaton file group identifier. |
| is_error_state | long | Boolean flag indicating whether error state. |
| is_ledger_on | long | Boolean flag indicating whether ledger on. |
| is_stable_state | long | Boolean flag indicating whether stable state. |
| last_exception | string | Last exception. |
| last_external_secret_check | datetime | Last external secret check. |
| last_restorable_point | datetime | Last restorable point. |
| last_state_change_time | datetime | Last state change time timestamp. |
| last_update_time | datetime | Last update time timestamp. |
| ledger_digest_storage_path | string | Ledger digest storage path. |
| ledger_digest_storage_type | string | Type classification for ledger digest storage. |
| managed_database_id | string | Managed database identifier. |
| managed_database_name | string | Managed database name. |
| managed_database_name_history | string | Managed database name history. |
| managed_server_id | string | Managed Instance identifier. |
| next_successor | long | Next successor. |
| owner_sid | string | Owner sid. |
| pending_hybridag_backup_metadata_fixup | long | Pending hybridag backup metadata fixup. |
| request_id | string | Request identifier used to correlate the operation. |
| resource_tags | string | Resource tags. |
| sql_database_id | long | SQL database identifier. |
| start_utc_date | datetime | Start utc date. |
| state | string | Current lifecycle or health state. |
| submit_resource_hydration | long | Submit resource hydration. |
| tail_log_backup_initiation_time | datetime | Tail log backup initiation time timestamp. |
| vldb_storage_coordinator_id | string | Vldb storage coordinator identifier. |
| xtp_enabled | long | In-Memory OLTP enabled. |

## MonManagedInstanceInfo — Managed Instance build and code-package details

**Purpose**: Managed Instance build and code-package details. Used to identify configuration, inventory, and latest known state for MI instances, databases, and related platform objects. Referenced in MI template areas: availability, general, performance.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| code_package_version | string | Code package version. |
| current_size_in_mb | long | Current size in mb. |
| database_id | long | Database identifier. |
| dbs_processed | long | Dbs processed. |
| done | bool | Boolean flag indicating whether done. |
| duration_ms | long | Duration in milliseconds. |
| error_number | long | SQL or platform error number. |
| error_severity | long | Error severity. |
| error_state | long | State value for error. |
| event | string | Event name emitted by the component. |
| failed_batch | string | Failed batch. |
| file_id | long | File identifier. |
| files_processed | long | Files processed. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| message | string | Human-readable message text. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| physical_database_name | string | Physical database name. |
| pools_processed | long | Pools processed. |
| script_name | string | Script name. |
| sessionName | string | Session Name. |

## MonManagedServerInstances — Managed Server Instances

**Purpose**: Managed Server Instances. Used to identify configuration, inventory, and latest known state for MI instances, databases, and related platform objects. Referenced in MI template areas: networking.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| admin_port | long | Admin port. |
| auxiliary_replica_count | long | Number of auxiliary replica. |
| capacities | string | Capacities. |
| code_package_version | string | Code package version. |
| concurrency_token | long | Concurrency token. |
| configuration_parameters | string | Configuration parameters. |
| create_mode | string | Create mode. |
| create_time | datetime | Creation timestamp. |
| db_role | string | Database role. |
| default_service_placement_value_requested | long | Default service placement value requested. |
| deployment_pinning_info_id | long | Deployment pinning info identifier. |
| dev_ops_logins | string | Dev ops logins. |
| dns_name | string | Dns name. |
| enable_infra_coordination | long | Enable infra coordination. |
| end_utc_date | datetime | End utc date. |
| fabric_application_uri | string | Fabric application uri. |
| fabric_cluster_dns_name | string | Fabric cluster dns name. |
| fabric_service_sequence | long | Fabric service sequence. |
| fabric_service_uri | string | Fabric service uri. |
| fsm_context_instance_name | string | Fsm context instance name. |
| fsm_extension_data | string | Fsm extension data. |
| fsm_instance_id | string | Fsm instance identifier. |
| fsm_timer_event_version | long | Fsm timer event version. |
| fsm_version | long | Fsm version. |
| global_transactions_port | long | Global transactions port. |
| is_error_state | long | Boolean flag indicating whether error state. |
| is_grip | long | Boolean flag indicating whether grip. |
| is_ipv6_enabled | long | Boolean flag indicating whether ipv6 enabled. |
| is_stable_state | long | Boolean flag indicating whether stable state. |
| is_wcow_instance | long | Boolean flag indicating whether wcow instance. |
| last_exception | string | Last exception. |
| last_state_change_time | datetime | Last state change time timestamp. |
| last_update_time | datetime | Last update time timestamp. |
| managed_server_id | string | Managed Instance identifier. |
| master_key_alg | string | Master key alg. |
| master_key_length | long | Master key length. |
| max_cpu_usage | long | Maximum CPU usage. |
| min_replica_count | long | Number of min replica. |
| name | string | Object or resource name. |
| next_successor | long | Next successor. |
| node_type | string | Type classification for node. |
| port | long | Port. |
| private_cluster_id | string | Private cluster identifier. |
| private_cluster_subscription_affinity_tag | string | Private cluster subscription affinity tag. |
| request_id | string | Request identifier used to correlate the operation. |
| requested_managed_disks | long | Requested managed disks. |
| rg_instancesettings_config_version | long | Resource governor instancesettings config version. |
| rg_isolation_settings | string | Resource governor isolation settings. |
| rg_size | string | Resource governor size. |
| server_property_overrides | string | Server property overrides. |
| service_level_objective | string | Service level objective. |
| should_creation_retry | long | Should creation retry. |
| sql_agent_state | long | State value for SQL agent. |
| sql_container_ip_reservation_set | string | SQL container ip reservation set. |
| sql_container_ip_reservation_set_id | string | SQL container ip reservation set identifier. |
| sql_container_ip_reservation_set_size | long | SQL container ip reservation set size. |
| sql_instance_id | string | SQL instance identifier. |
| ssb_port | long | Service Broker port. |
| start_utc_date | datetime | Start utc date. |
| state | string | Current lifecycle or health state. |
| target_application_type_version | string | Target application type version. |
| target_replica_count | long | Number of target replica. |
| target_service_level_objective | string | Target service level objective. |
| target_tenant_ring_name | string | Target tenant ring name. |
| tenant_ring_name | string | Tenant ring name. |
| tenant_ring_placement_history | string | Tenant ring placement history. |
| type | string | Type. |
| ucs_port | long | UCS port. |
| version_edition | string | Version edition. |
| vm_size | string | Vm size. |
| worker_service_affinity_tag | string | Worker service affinity tag. |

## MonManagedServers — Managed Instance inventory and configuration snapshot

**Purpose**: Managed Instance inventory and configuration snapshot. Used to identify configuration, inventory, and latest known state for MI instances, databases, and related platform objects. Referenced in MI template areas: availability, backup-restore, general, networking, performance. Often used during backup or restore investigations.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| additional_replica_storage_account_name | string | Additional replica storage account name. |
| additional_replica_storage_container_name | string | Additional replica storage container name. |
| admin_login_change_time | datetime | Admin login change time timestamp. |
| admin_login_name | string | Admin login name. |
| admin_login_password | string | Admin login password. |
| auto_tuning_settings_id | string | Auto tuning settings identifier. |
| azure_dns_record_name | string | Azure dns record name. |
| azure_provisioning_dns_record_name | string | Azure provisioning dns record name. |
| azure_secondary_dns_record_name | string | Azure secondary dns record name. |
| backup_storage_account_name | string | Backup storage account name. |
| backup_storage_account_type | string | Type classification for backup storage account. |
| backup_storage_container_name | string | Backup storage container name. |
| backup_storage_usage_gb | long | Backup storage usage gb. |
| bill_sql_server_license | long | Bill SQL server license. |
| bill_vcores | long | Bill vcores. |
| billing_start_time | datetime | Billing start time timestamp. |
| code_package_version | string | Code package version. |
| collation | string | Collation. |
| concurrency_token | long | Concurrency token. |
| configuration_parameters | string | Configuration parameters. |
| create_mode | string | Create mode. |
| create_time | datetime | Creation timestamp. |
| custom_maintenance_window_scheduler_pattern | string | Custom maintenance window scheduler pattern. |
| customer_subscription_id | string | Customer subscription identifier. |
| db_role_placement_rules | string | Database role placement rules. |
| dns_zone | string | Dns zone. |
| dropped_date | datetime | Dropped date. |
| edition | string | Edition. |
| encryption_identity_id | string | Encryption identity identifier. |
| encryption_protector_type | string | Type classification for encryption protector. |
| end_utc_date | datetime | End utc date. |
| federated_client_id | string | Federated client identifier. |
| fsm_context_instance_name | string | Fsm context instance name. |
| fsm_extension_data | string | Fsm extension data. |
| fsm_instance_id | string | Fsm instance identifier. |
| fsm_timer_event_version | long | Fsm timer event version. |
| fsm_version | long | Fsm version. |
| hardware_family | string | Hardware family. |
| identity_client_id | string | Identity client identifier. |
| identity_principal_id | string | Identity principal identifier. |
| identity_tenant_id | string | Identity tenant identifier. |
| identity_type | long | Type classification for identity. |
| identity_url | string | Identity url. |
| internal_private_dns_record_name | string | Internal private dns record name. |
| internal_public_dns_record_name | string | Internal public dns record name. |
| is_azure_rbac_enabled | long | Boolean flag indicating whether azure rbac enabled. |
| is_error_state | long | Boolean flag indicating whether error state. |
| is_freemium | long | Boolean flag indicating whether freemium. |
| is_grip | long | Boolean flag indicating whether grip. |
| is_mi_link_disaster_recovery_only | long | Boolean flag indicating whether MI link disaster recovery only. |
| is_multi_nic_wcow | long | Boolean flag indicating whether multi nic wcow. |
| is_stable_state | long | Boolean flag indicating whether stable state. |
| is_versioned_instance | long | Boolean flag indicating whether versioned instance. |
| is_wcow_managed_server | long | Boolean flag indicating whether wcow managed server. |
| key_id | string | Key identifier. |
| last_backup_storage_usage_event_timestamp | datetime | Last backup storage usage event timestamp. |
| last_encryption_protector_update | datetime | Last encryption protector update. |
| last_exception | string | Last exception. |
| last_start_time | datetime | Last start time timestamp. |
| last_state_billability_change_time | datetime | Last state billability change time timestamp. |
| last_state_change_time | datetime | Last state change time timestamp. |
| last_stop_time | datetime | Last stop time timestamp. |
| last_update_time | datetime | Last update time timestamp. |
| last_xact_outcome_cleanup_time | datetime | Last xact outcome cleanup time timestamp. |
| log_storage_account_name | string | Log storage account name. |
| log_storage_container_name | string | Log storage container name. |
| maintenance_policy_id | string | Maintenance policy identifier. |
| managed_instance_pool_id | string | Managed instance pool identifier. |
| managed_server_id | string | Managed Instance identifier. |
| minimal_tls_version | long | Minimal tls version. |
| name | string | Object or resource name. |
| next_successor | long | Next successor. |
| physical_instance_name | string | Physical instance name. |
| preserved_service_master_key | string | Preserved service master key. |
| private_cluster_id | string | Private cluster identifier. |
| private_cluster_tenant_ring_name | string | Private cluster tenant ring name. |
| proxy_override | string | Proxy override. |
| public_ip | long | Public ip. |
| read_scale_units | long | Read scale units. |
| referral_id | string | Referral identifier. |
| regional_authentication_endpoint | string | Regional authentication endpoint. |
| request_id | string | Request identifier used to correlate the operation. |
| requested_aad_only_authentication | long | Requested Azure AD only authentication. |
| requested_backup_storage_account_type | string | Type classification for requested backup storage account. |
| requested_external_admin_login_name | string | Requested external admin login name. |
| requested_external_admin_login_sid | string | Requested external admin login sid. |
| requested_federated_client_id | string | Requested federated client identifier. |
| requested_managed_disks | long | Requested managed disks. |
| requested_service_principal_type | string | Type classification for requested service principal. |
| requested_tenant_id | string | Requested tenant identifier. |
| requested_user_provided_principal_type | string | Type classification for requested user provided principal. |
| reserved_storage_iops | long | Reserved storage IOPS. |
| reserved_storage_size_gb | long | Reserved storage size gb. |
| reserved_storage_throughput_mbps | long | Reserved storage throughput mbps. |
| resource_tags | string | Resource tags. |
| restore_point_in_time | datetime | Restore point in time timestamp. |
| rg_database_settings_overrides | string | Resource governor database settings overrides. |
| rg_instance_settings_overrides | string | Resource governor instance settings overrides. |
| rg_slo_property_bag_overrides | string | Resource governor slo property bag overrides. |
| server_slice_binding_name | string | Server slice binding name. |
| service_level_objective | string | Service level objective. |
| source_managed_server_name | string | Source managed server name. |
| sql_server_license | string | SQL server license. |
| start_utc_date | datetime | Start utc date. |
| state | string | Current lifecycle or health state. |
| state_billability | long | State billability. |
| stop_mode | string | Stop mode. |
| storage_account_name | string | Storage account name. |
| storage_container_name | string | Storage container name. |
| storage_type | string | Type classification for storage. |
| subnet_id | string | Subnet identifier. |
| telemetry_storage_account_name | string | Telemetry storage account name. |
| telemetry_storage_container_name | string | Telemetry storage container name. |
| timezone_id | string | Timezone identifier. |
| trace_flags | string | Trace flags. |
| vcore_count | long | Number of vCore. |
| version_edition | string | Version edition. |
| vldb_storage_connectivity_id | string | Vldb storage connectivity identifier. |
| vnet_dns_record_name | string | Vnet dns record name. |
| zone_redundant | long | Zone redundant. |

# 2. Performance & Resources

## MonAutomaticTuning — Automatic Tuning

**Purpose**: Automatic Tuning. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| advisor_actual_state | bool | Boolean flag indicating whether advisor actual state. |
| advisor_desired_state | bool | Boolean flag indicating whether advisor desired state. |
| advisor_desired_tuning_mode | long | Advisor desired tuning mode. |
| advisor_id | long | Advisor identifier. |
| baseline_cpu_time_average | long | Baseline CPU time average. |
| baseline_cpu_time_std_dev | long | Baseline CPU time std dev. |
| check_count | long | Number of check. |
| code_package_version | string | Code package version. |
| corrected_count | long | Number of corrected. |
| cpu_time_average | long | CPU time average. |
| cpu_time_std_dev | long | CPU time std dev. |
| current_plan_cpu_time_average | real | Current plan CPU time average. |
| current_plan_cpu_time_stddev | real | Current plan CPU time stddev. |
| current_plan_error_count | long | Number of current plan error. |
| current_plan_execution_count | long | Number of current plan execution. |
| current_plan_id | long | Current plan identifier. |
| database_id | long | Database identifier. |
| database_tuning_mode | long | Database tuning mode. |
| detected_count | long | Number of detected. |
| detection_end_time_date | long | Detection end time date. |
| detection_end_time_ms | long | Detection end time ms in milliseconds. |
| detection_start_date | long | Detection start date. |
| detection_start_time_ms | long | Detection start time ms in milliseconds. |
| dropped_count | long | Number of dropped. |
| duration | long | Duration. |
| error_code | long | Numeric error code for the failure or event. |
| error_count | long | Number of error. |
| error_number | long | SQL or platform error number. |
| error_severity | long | Error severity. |
| error_state | long | State value for error. |
| estimated_cpu_time_gain | long | Estimated CPU time gain. |
| event | string | Event name emitted by the component. |
| execution_count | long | Number of execution. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| initial_stats_update_back_off_delay_minutes | long | Initial stats update back off delay minutes. |
| initial_verificaiton_period_minutes | long | Initial verificaiton period minutes. |
| internal_status_code | long | Internal status code. |
| is_check_resubmitted | bool | Boolean flag indicating whether check resubmitted. |
| is_correction_enabled | bool | Boolean flag indicating whether correction enabled. |
| is_detection_enabled | bool | Boolean flag indicating whether detection enabled. |
| is_error_prone | bool | Boolean flag indicating whether error prone. |
| is_regression_corrected | bool | Boolean flag indicating whether regression corrected. |
| is_regression_detected | bool | Boolean flag indicating whether regression detected. |
| last_error_number | long | Last error number. |
| last_good_plan_cpu_time_average | real | Last good plan CPU time average. |
| last_good_plan_cpu_time_stddev | real | Last good plan CPU time stddev. |
| last_good_plan_error_count | long | Number of last good plan error. |
| last_good_plan_execution_count | long | Number of last good plan execution. |
| last_good_plan_id | long | Last good plan identifier. |
| logical_database_guid | string | Logical database guid. |
| logical_database_name | string | Logical database name. |
| max_event_list_size | long | Maximum event list size. |
| max_new_plan_aborted_count | long | Number of max new plan aborted. |
| max_queue_size | long | Maximum queue size. |
| max_stats_update_back_off_delay_minutes | long | Maximum stats update back off delay minutes. |
| max_verification_period_minutes | long | Maximum verification period minutes. |
| max_verification_queue_size | long | Maximum verification queue size. |
| means_ratio | real | Means ratio. |
| min_best_execution_count | long | Number of min best execution. |
| min_estimated_cpu_gain_seconds | long | Minimum estimated CPU gain seconds. |
| min_new_plan_execution_count | long | Number of min new plan execution. |
| minutes_to_consider | long | Minutes to consider. |
| new_database_advisor_on_off_flags | long | New database advisor on off flags. |
| new_database_advisor_set_by_system_flags | long | New database advisor set by system flags. |
| new_database_advisor_system_disabled_flags | long | New database advisor system disabled flags. |
| new_database_advisor_user_override_flags | long | New database advisor user override flags. |
| new_database_tuning_mode | string | New database tuning mode. |
| new_database_tuning_mode_set_by_system | bool | Boolean flag indicating whether new database tuning mode set by system. |
| new_server_advisor_flags | long | New server advisor flags. |
| new_server_tuning_mode | string | New server tuning mode. |
| nsp | string | Nsp. |
| old_database_advisor_on_off_flags | long | Old database advisor on off flags. |
| old_database_advisor_set_by_system_flags | long | Old database advisor set by system flags. |
| old_database_advisor_system_disabled_flags | long | Old database advisor system disabled flags. |
| old_database_advisor_user_override_flags | long | Old database advisor user override flags. |
| old_database_tuning_mode | string | Old database tuning mode. |
| old_database_tuning_mode_set_by_system | bool | Boolean flag indicating whether old database tuning mode set by system. |
| old_server_advisor_flags | long | Old server advisor flags. |
| old_server_tuning_mode | string | Old server tuning mode. |
| option_id | long | Option identifier. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| phase_code | string | Phase code. |
| plan_comparison_process_start_date | long | Plan comparison process start date. |
| plan_comparison_process_start_time_ms | long | Plan comparison process start time ms in milliseconds. |
| plan_id | long | Plan identifier. |
| query_id | long | Query identifier. |
| queue_count | long | Number of queue. |
| reason_code | string | Reason code. |
| recheck_after_executions | long | Recheck after executions. |
| rejection_threshold | real | Rejection threshold. |
| replica_group_id | long | Replica group identifier. |
| sessionName | string | Session Name. |
| sigmas | real | Sigmas. |
| state_code | string | State code. |
| status | string | Current status reported by the component. |
| stddev_ratio | real | Stddev ratio. |
| submitted_count | long | Number of submitted. |
| submitted_with_priority | bool | Boolean flag indicating whether submitted with priority. |
| total_elapsed_time_ms | long | Total elapsed time ms. |
| total_logical_reads | long | Total logical reads. |
| total_logical_writes | long | Total logical writes. |
| total_physical_reads | long | Total physical reads. |
| total_worker_time_ms | long | Total worker time ms. |
| verification_end_date | long | Verification end date. |
| verification_end_time_ms | long | Verification end time ms in milliseconds. |
| verification_start_date | long | Verification start date. |
| verification_start_time_ms | long | Verification start time ms in milliseconds. |
| welch_test_result | string | Welch test result. |

## MonCounterFiveMinute — Counter Five Minute

**Purpose**: Counter Five Minute. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| CounterName | string | Number of Counter Name. |
| CounterValue | real | Number of Counter Value. |
| MaxVal | real | Max Val. |
| MinVal | real | Min Val. |
| OneBoxClusterId | string | One Box Cluster Id. |

## MonCounterOneMinute — Counter One Minute

**Purpose**: Counter One Minute. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: availability, backup-restore, networking, performance. Often used during backup or restore investigations.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| CounterName | string | Number of Counter Name. |
| CounterValue | real | Number of Counter Value. |
| MaxVal | real | Max Val. |
| MinVal | real | Min Val. |
| OneBoxClusterId | string | One Box Cluster Id. |

## MonDmCloudDatabaseWaitStats — DM Cloud Database Wait Stats

**Purpose**: DM Cloud Database Wait Stats. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: performance. Often used to explain wait or latency patterns.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| ResourcePoolName | string | Resource Pool Name. |
| code_package_version | string | Code package version. |
| database_id | long | Database identifier. |
| database_name | string | Database name. |
| delta_is_valid | long | Delta is valid. |
| delta_max_wait_time_ms | long | Delta max wait time ms in milliseconds. |
| delta_signal_wait_time_ms | long | Delta signal wait time ms in milliseconds. |
| delta_wait_time_ms | long | Delta wait time ms in milliseconds. |
| delta_waiting_tasks_count | long | Number of delta waiting tasks. |
| end_utc_date | datetime | End utc date. |
| max_wait_time_ms | long | Maximum wait time ms. |
| physical_database_guid | string | Physical database guid. |
| server_name | string | Managed Instance server name. |
| signal_wait_time_ms | long | Signal wait time ms in milliseconds. |
| start_utc_date | datetime | Start utc date. |
| wait_time_ms | long | Wait time in milliseconds. |
| wait_type | string | Wait type name. |
| waiting_tasks_count | long | Number of waiting tasks. |

## MonDmDbResourceGovernance — DM Database Resource Governance

**Purpose**: DM Database Resource Governance. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: availability, general, performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| bufferpool_extension_size_gb | long | Bufferpool extension size gb. |
| cap_cpu | long | Cap CPU. |
| checkpoint_rate_io | long | Checkpoint rate I/O. |
| checkpoint_rate_mbps | long | Checkpoint rate mbps. |
| code_package_version | string | Code package version. |
| compute_units | real | Compute units. |
| consolidation_type | string | Type classification for consolidation. |
| cpu_core_ratio | real | CPU core ratio. |
| cpu_limit | long | CPU limit. |
| database_id | long | Database identifier. |
| database_name | string | Database name. |
| db_file_growth_in_mb | long | Database file growth in mb. |
| default_db_max_size_in_mb | long | Default database max size in mb. |
| downgrade_date | datetime | Downgrade date. |
| downgrade_date_utc | datetime | Downgrade date utc. |
| downgrade_reason | string | Downgrade reason. |
| dtu_limit | long | Dtu limit. |
| end_utc_date | datetime | End utc date. |
| geo_seeding_flow_control_limit_bytes | long | Geo seeding flow control limit size in bytes. |
| geo_seeding_use_compression | long | Geo seeding use compression. |
| govern_background_io | long | Govern background I/O. |
| govern_db_memory_in_resource_pool | long | Govern database memory in resource pool. |
| hk_ckpt_file_space_limit_in_mb | long | Hk ckpt file space limit in mb. |
| hk_log_space_limit_percent | long | Hk log space limit percentage. |
| initial_db_file_size_in_mb | long | Initial database file size in mb. |
| instance_cap_cpu | long | Instance cap CPU. |
| instance_max_log_rate | long | Instance max log rate. |
| instance_max_worker_threads | long | Instance max worker threads. |
| instance_temp_db_log_byte_factor | real | Instance temp database log byte factor. |
| job_low_memory_signal_threshold_mb | long | Job low memory signal threshold mb. |
| last_updated_date | datetime | Last updated date. |
| last_updated_date_utc | datetime | Last updated date utc. |
| local_seeding_flow_control_limit_bytes | long | Local seeding flow control limit size in bytes. |
| local_seeding_use_compression | long | Local seeding use compression. |
| log_size_in_mb | long | Log size in mb. |
| logical_database_guid | string | Logical database guid. |
| max_cpu | long | Maximum CPU. |
| max_db_max_size_in_mb | long | Maximum database max size in mb. |
| max_db_memory | long | Maximum database memory. |
| max_dop | long | Maximum dop. |
| max_memory | long | Maximum memory. |
| max_memory_grant | string | Maximum memory grant. |
| max_sessions | long | Maximum sessions. |
| max_transaction_size | long | Maximum transaction size. |
| min_cores | long | Minimum cores. |
| min_cpu | long | Minimum CPU. |
| min_db_max_size_in_mb | long | Minimum database max size in mb. |
| min_memory | long | Minimum memory. |
| min_sos_gap_with_job_mem_limit_in_mb | long | Minimum sos gap with job memory limit in mb. |
| passive_broker_free_memory_gap_percent | long | Passive broker free memory gap percentage. |
| physical_database_guid | string | Physical database guid. |
| pool_max_io | long | Pool max I/O. |
| pool_max_log_rate | long | Pool max log rate. |
| primary_bucket_depth_cpu | long | Primary bucket depth CPU. |
| primary_bucket_fill_rate_cpu | long | Primary bucket fill rate CPU. |
| primary_bucket_max_cpu | real | Primary bucket max CPU. |
| primary_bucket_min_cpu | real | Primary bucket min CPU. |
| primary_checkpoint_page_limit | long | Primary checkpoint page limit. |
| primary_group_id | long | Primary group identifier. |
| primary_group_max_cpu | real | Primary group max CPU. |
| primary_group_max_io | long | Primary group max I/O. |
| primary_group_max_outbound_connection_workers | long | Primary group max outbound connection workers. |
| primary_group_max_workers | long | Primary group max workers. |
| primary_group_min_cpu | real | Primary group min CPU. |
| primary_group_min_io | long | Primary group min I/O. |
| primary_log_commit_fee | long | Primary log commit fee. |
| primary_log_max_idle_credit | long | Primary log max idle credit. |
| primary_log_rollback_factor | long | Primary log rollback factor. |
| primary_log_temp_db_byte_factor | real | Primary log temp database byte factor. |
| primary_max_idle_credit_io | long | Primary max idle credit I/O. |
| primary_max_log_rate | long | Primary max log rate. |
| primary_min_log_rate | long | Primary min log rate. |
| primary_pool_max_outbound_connection_workers | long | Primary pool max outbound connection workers. |
| primary_pool_max_workers | long | Primary pool max workers. |
| primary_token_bucket_depth_io | long | Primary token bucket depth I/O. |
| primary_token_bucket_fill_rate_io | long | Primary token bucket fill rate I/O. |
| primary_token_bucket_max_io | long | Primary token bucket max I/O. |
| primary_token_bucket_min_io | long | Primary token bucket min I/O. |
| recovery_interval_ms | long | Recovery interval ms in milliseconds. |
| replica_type | long | Type classification for replica. |
| secondary_bucket_depth_cpu | long | Secondary bucket depth CPU. |
| secondary_bucket_fill_rate_cpu | long | Secondary bucket fill rate CPU. |
| secondary_bucket_max_cpu | real | Secondary bucket max CPU. |
| secondary_bucket_min_cpu | real | Secondary bucket min CPU. |
| secondary_checkpoint_page_limit | long | Secondary checkpoint page limit. |
| secondary_group_id | long | Secondary group identifier. |
| secondary_group_max_cpu | real | Secondary group max CPU. |
| secondary_group_max_io | long | Secondary group max I/O. |
| secondary_group_max_outbound_connection_workers | long | Secondary group max outbound connection workers. |
| secondary_group_max_workers | long | Secondary group max workers. |
| secondary_group_min_cpu | real | Secondary group min CPU. |
| secondary_group_min_io | long | Secondary group min I/O. |
| secondary_log_commit_fee | long | Secondary log commit fee. |
| secondary_log_max_idle_credit | long | Secondary log max idle credit. |
| secondary_log_rollback_factor | long | Secondary log rollback factor. |
| secondary_log_temp_db_byte_factor | real | Secondary log temp database byte factor. |
| secondary_max_idle_credit_io | long | Secondary max idle credit I/O. |
| secondary_max_log_rate | long | Secondary max log rate. |
| secondary_min_log_rate | long | Secondary min log rate. |
| secondary_pool_max_outbound_connection_workers | long | Secondary pool max outbound connection workers. |
| secondary_pool_max_workers | long | Secondary pool max workers. |
| secondary_token_bucket_depth_io | long | Secondary token bucket depth I/O. |
| secondary_token_bucket_fill_rate_io | long | Secondary token bucket fill rate I/O. |
| secondary_token_bucket_max_io | long | Secondary token bucket max I/O. |
| secondary_token_bucket_min_io | long | Secondary token bucket min I/O. |
| seeding_backup_buffer_count | long | Number of seeding backup buffer. |
| seeding_backup_buffer_size_bytes | long | Seeding backup buffer size size in bytes. |
| server_name | string | Managed Instance server name. |
| slo_name | string | Slo name. |
| slo_violation_cpu_min_pct | real | Slo violation CPU min pct. |
| slo_violation_detection_interval_secs | long | Slo violation detection interval secs. |
| slo_violation_io_min_iops | long | Slo violation I/O min IOPS. |
| slo_violation_log_min_rate | long | Slo violation log min rate. |
| start_utc_date | datetime | Start utc date. |
| total_cpu_usage_ms | long | Total CPU usage ms. |
| user_data_directory_space_quota_mb | long | User data directory space quota mb. |
| user_data_directory_space_usage_mb | long | User data directory space usage mb. |
| volume_external_xstore_iops | long | Volume external xstore IOPS. |
| volume_local_iops | long | Volume local IOPS. |
| volume_managed_xstore_iops | long | Volume managed xstore IOPS. |
| volume_type_external_xstore_iops | long | Volume type external xstore IOPS. |
| volume_type_local_iops | long | Volume type local IOPS. |
| volume_type_managed_xstore_iops | long | Volume type managed xstore IOPS. |
| volume_type_rbio_data_iops | long | Volume type rbio data IOPS. |

## MonDmIoVirtualFileStats — DM I/O Virtual File Stats

**Purpose**: DM I/O Virtual File Stats. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: availability, backup-restore, general, performance. Often used during backup or restore investigations.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| SourceTable | string | Source Table. |
| code_package_version | string | Code package version. |
| database_id | long | Database identifier. |
| db_name | string | Database name. |
| delta_io_stall | long | Delta I/O stall. |
| delta_io_stall_queued_read_ms | long | Delta I/O stall queued read ms in milliseconds. |
| delta_io_stall_queued_write_ms | long | Delta I/O stall queued write ms in milliseconds. |
| delta_io_stall_read_ms | long | Delta I/O stall read ms in milliseconds. |
| delta_io_stall_write_ms | long | Delta I/O stall write ms in milliseconds. |
| delta_is_valid | long | Delta is valid. |
| delta_num_of_bytes_read | long | Delta num of size in bytes read. |
| delta_num_of_bytes_written | long | Delta num of size in bytes written. |
| delta_num_of_reads | long | Delta num of reads. |
| delta_num_of_writes | long | Delta num of writes. |
| delta_size_on_disk_bytes | long | Delta size on disk size in bytes. |
| end_utc_date | datetime | End utc date. |
| file_handle | string | File handle. |
| file_id | long | File identifier. |
| growth | long | Growth. |
| io_stall | long | I/O stall. |
| io_stall_queued_read_ms | long | I/O stall queued read ms in milliseconds. |
| io_stall_queued_write_ms | long | I/O stall queued write ms in milliseconds. |
| io_stall_read_ms | long | I/O stall read ms in milliseconds. |
| io_stall_write_ms | long | I/O stall write ms in milliseconds. |
| is_primary_replica | long | Boolean flag indicating whether primary replica. |
| is_remote | long | Boolean flag indicating whether remote. |
| logical_database_id | string | Logical database identifier. |
| max_size_mb | long | Maximum size mb. |
| num_of_bytes_read | long | Num of size in bytes read. |
| num_of_bytes_written | long | Num of size in bytes written. |
| num_of_reads | long | Num of reads. |
| num_of_writes | long | Num of writes. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| sample_ms | long | Sample ms in milliseconds. |
| size_on_disk_bytes | long | Size on disk size in bytes. |
| spaceused_mb | long | Spaceused mb. |
| start_utc_date | datetime | Start utc date. |
| storage_type | long | Type classification for storage. |
| type_desc | string | Type desc. |

## MonDmOsBPoolPerfCounters — DM OS BPool Perf Counters

**Purpose**: DM OS BPool Perf Counters. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| cntr_value | long | Cntr value. |
| code_package_version | string | Code package version. |
| counter_name | string | Counter name. |
| end_utc_date | datetime | End utc date. |
| instance_name | string | Instance name. |
| start_utc_date | datetime | Start utc date. |

## MonDmOsExceptionStats — DM OS Exception Stats

**Purpose**: DM OS Exception Stats. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: backup-restore. Often used during backup or restore investigations.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| code_package_version | string | Code package version. |
| delta_exception_count | long | Number of delta exception. |
| delta_is_valid | long | Delta is valid. |
| end_utc_date | datetime | End utc date. |
| exception_count | long | Number of exception. |
| exception_id | long | Exception identifier. |
| start_utc_date | datetime | Start utc date. |

## MonDmOsMemoryClerks — DM OS Memory Clerks

**Purpose**: DM OS Memory Clerks. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| awe_allocated_kb | long | Awe allocated kb. |
| code_package_version | string | Code package version. |
| delta_awe_allocated_kb | long | Delta awe allocated kb. |
| delta_is_valid | long | Delta is valid. |
| delta_page_size_in_bytes | long | Delta page size in size in bytes. |
| delta_pages_kb | long | Delta pages kb. |
| delta_shared_memory_committed_kb | long | Delta shared memory committed kb. |
| delta_shared_memory_reserved_kb | long | Delta shared memory reserved kb. |
| delta_virtual_memory_committed_kb | long | Delta virtual memory committed kb. |
| delta_virtual_memory_reserved_kb | long | Delta virtual memory reserved kb. |
| end_utc_date | datetime | End utc date. |
| host_address | string | Host address. |
| memory_clerk_address | string | Memory clerk address. |
| memory_node_id | long | Memory node identifier. |
| name | string | Object or resource name. |
| page_allocator_address | string | Page allocator address. |
| page_size_in_bytes | long | Page size in size in bytes. |
| pages_kb | long | Pages kb. |
| parent_memory_broker_type | string | Type classification for parent memory broker. |
| shared_memory_committed_kb | long | Shared memory committed kb. |
| shared_memory_reserved_kb | long | Shared memory reserved kb. |
| start_utc_date | datetime | Start utc date. |
| type | string | Type. |
| virtual_memory_committed_kb | long | Virtual memory committed kb. |
| virtual_memory_reserved_kb | long | Virtual memory reserved kb. |

## MonDmOsSpinlockStats — DM OS Spinlock Stats

**Purpose**: DM OS Spinlock Stats. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| backoffs | long | Backoffs. |
| code_package_version | string | Code package version. |
| collisions | long | Collisions. |
| delta_backoffs | long | Delta backoffs. |
| delta_collisions | long | Delta collisions. |
| delta_is_valid | long | Delta is valid. |
| delta_sleep_time | long | Delta sleep time timestamp. |
| delta_spins | long | Delta spins. |
| end_utc_date | datetime | End utc date. |
| name | string | Object or resource name. |
| sleep_time | long | Sleep time timestamp. |
| spins | long | Spins. |
| spins_per_collision | float | Spins per collision. |
| start_utc_date | datetime | Start utc date. |

## MonDmRealTimeResourceStats — Database-level real-time resource usage

**Purpose**: Database-level real-time resource usage. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: availability, general, performance. Often used for sizing or billing-related investigations.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| allocated_storage_mb | long | Allocated storage mb. |
| attach_activity_id | string | Attach activity identifier. |
| attach_activity_id_xfer | string | Attach activity id xfer. |
| avg_cpu_percent | real | Average CPU utilization percentage. |
| avg_data_background_io_percent | real | Average data background I/O percentage. |
| avg_data_io_percent | real | Average data I/O utilization percentage. |
| avg_instance_cpu_percent | real | Average instance CPU percentage. |
| avg_instance_memory_percent | real | Average instance memory percentage. |
| avg_log_write_percent | real | Average log write utilization percentage. |
| avg_login_rate_percent | real | Average login rate percentage. |
| avg_memory_usage_percent | real | Average memory utilization percentage. |
| avg_normalized_data_io_percent | real | Average normalized data I/O percentage. |
| avg_sos_instance_cpu_percent | real | Average sos instance CPU percentage. |
| code_package_version | string | Code package version. |
| cpu_cap_in_sec | real | CPU cap in sec. |
| cpu_limit | real | CPU limit. |
| database_id | long | Database identifier. |
| database_name | string | Database name. |
| delta_background_write_ios_arrived_total | long | Delta background write ios arrived total. |
| delta_ios_completed_total | long | Delta ios completed total. |
| dtu_limit | long | Dtu limit. |
| dw_logical_node_id | string | Billing warehouse logical node identifier. |
| end_time | datetime | End timestamp. |
| event | string | Event name emitted by the component. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| io_cap | real | I/O cap. |
| ios_completed_total | long | Ios completed total. |
| log_bytes_used_total | long | Log size in bytes used total. |
| log_cap | real | Log cap. |
| max_session_percent | real | Maximum session percentage. |
| max_worker_percent | real | Maximum worker percentage. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| physical_database_guid | string | Physical database guid. |
| process_id | long | Process identifier. |
| profiler_trace_triggered | bool | Boolean flag indicating whether profiler trace triggered. |
| progressive_group_id | long | Progressive group identifier. |
| replica_role | long | Replica role. |
| replica_type | long | Type classification for replica. |
| server_name | string | Managed Instance server name. |
| sessionName | string | Session Name. |
| slo_name | string | Slo name. |
| stats_reset | long | Stats reset. |
| system_thread_id | long | System thread identifier. |
| total_cpu_usage_ms | long | Total CPU usage ms. |
| total_memory_usage_kb | long | Total memory usage kb. |
| used_storage_mb | long | Used storage mb. |
| xtp_storage_percent | real | In-Memory OLTP storage percentage. |

## MonDmTempDbFileSpaceUsage — DM Temp Database File Space Usage

**Purpose**: DM Temp Database File Space Usage. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| allocated_extent_page_count | long | Number of allocated extent page. |
| code_package_version | string | Code package version. |
| database_id | long | Database identifier. |
| end_utc_date | datetime | End utc date. |
| file_id | long | File identifier. |
| filegroup_id | long | Filegroup identifier. |
| internal_object_reserved_page_count | long | Number of internal object reserved page. |
| mixed_extent_page_count | long | Number of mixed extent page. |
| modified_extent_page_count | long | Number of modified extent page. |
| start_utc_date | datetime | Start utc date. |
| total_page_count | long | Number of total page. |
| unallocated_extent_page_count | long | Number of unallocated extent page. |
| user_object_reserved_page_count | long | Number of user object reserved page. |
| version_store_reserved_page_count | long | Number of version store reserved page. |

## MonDmTranActiveTransactions — DM Tran Active Transactions

**Purpose**: DM Tran Active Transactions. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: availability, performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| accessed_tempdb | long | Accessed tempdb. |
| code_package_version | string | Code package version. |
| cpu_time_in_ms | long | CPU time in ms in milliseconds. |
| database_id | long | Database identifier. |
| end_utc_date | datetime | End utc date. |
| memory_usage_kb | long | Memory usage kb. |
| program_name | string | Program name. |
| row_count | long | Number of row. |
| session_id | long | Session identifier. |
| session_type | string | Type classification for session. |
| start_utc_date | datetime | Start utc date. |
| status | string | Current status reported by the component. |
| total_elapsed_time_in_ms | long | Total elapsed time in ms. |
| total_scheduled_time_in_ms | long | Total scheduled time in ms. |
| transaction_begin_time | datetime | Transaction begin time timestamp. |
| transaction_id | long | Transaction identifier. |
| transaction_state | long | State value for transaction. |
| transaction_type | long | Type classification for transaction. |
| user_db_name | string | User database name. |

## MonDmUserActivityDetection — DM User Activity Detection

**Purpose**: DM User Activity Detection. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| TridentServerType | string | Trident Server Type. |
| action | long | Action. |
| active_login | long | Active login. |
| active_request | long | Active request. |
| active_worker | long | Active worker. |
| adjust_interval_enabled | bool | Boolean flag indicating whether adjust interval enabled. |
| attach_activity_id | string | Attach activity identifier. |
| attach_activity_id_xfer | string | Attach activity id xfer. |
| backoff_deactivation_until_min | long | Backoff deactivation until min. |
| code_package_version | string | Code package version. |
| cpu_comparison | real | CPU comparison. |
| cpu_historyS | long | CPU history S. |
| cpu_threshold | real | CPU threshold. |
| criteria_type_name | string | Criteria type name. |
| current | long | Current. |
| database_name | string | Database name. |
| db_interval_min | long | Database interval min. |
| db_interval_min_old | long | Database interval min old. |
| deactivation_count | long | Number of deactivation. |
| deactivation_interval_min | long | Deactivation interval min. |
| deactivations_throttled | bool | Boolean flag indicating whether deactivations throttled. |
| deflation_historyS | long | Deflation history S. |
| deflation_status | bool | Boolean flag indicating whether deflation status. |
| deflation_threshold_slo | string | Deflation threshold slo. |
| delta_login | long | Delta login. |
| delta_request_completed | long | Delta request completed. |
| delta_request_throttled | long | Delta request throttled. |
| delta_timeMs | long | Delta time Ms. |
| delta_total_request_throttled | long | Delta total request throttled. |
| duration_min | long | Duration min. |
| duration_ms | long | Duration in milliseconds. |
| elapsed_cputime | long | Elapsed cputime. |
| end_of_predicted_activity | string | End of predicted activity. |
| error | bool | Error text captured for the event or operation. |
| error_message | string | Error message. |
| error_number | long | SQL or platform error number. |
| error_state | long | State value for error. |
| event | string | Event name emitted by the component. |
| fast_physical_pause_min | long | Fast physical pause min. |
| force | bool | Boolean flag indicating whether force. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| http_code | long | Http code. |
| inactive_duration_min | long | Inactive duration min. |
| informational | bool | Boolean flag indicating whether informational. |
| instance_rg_slo_guid | string | Instance resource governor slo guid. |
| instance_rg_slo_name | string | Instance resource governor slo name. |
| io_comparison | real | I/O comparison. |
| io_historyS | long | I/O history S. |
| io_threshold | long | I/O threshold. |
| is_active | bool | Boolean flag indicating whether active. |
| is_db_old | long | Boolean flag indicating whether database old. |
| is_fast_physical_pause_enabled | bool | Boolean flag indicating whether fast physical pause enabled. |
| is_logically_paused | bool | Boolean flag indicating whether logically paused. |
| is_primary_replica | bool | Boolean flag indicating whether primary replica. |
| is_proactive_activation | bool | Boolean flag indicating whether proactive activation. |
| is_spinnaker_db | bool | Boolean flag indicating whether spinnaker database. |
| is_success | bool | Boolean flag indicating whether success. |
| json_message | string | Json message. |
| last_active | long | Last active. |
| last_cpu_activity_minutes | long | Last CPU activity minutes. |
| last_cpu_consumption | long | Last CPU consumption. |
| last_deactivated | datetime | Last deactivated. |
| last_deactivated_old | datetime | Last deactivated old. |
| last_login_timestamp | long | Last login timestamp. |
| last_request_guid | string | Last request guid. |
| log_comparison | real | Log comparison. |
| log_historyS | long | Log history S. |
| log_level | long | Log level. |
| log_threshold | long | Log threshold. |
| logical_database_guid | string | Logical database guid. |
| logical_database_id | string | Logical database identifier. |
| mem_comparison | long | Memory comparison. |
| mem_historyS | long | Memory history S. |
| mem_threshold | long | Memory threshold. |
| message | string | Human-readable message text. |
| min_since_last_deactivation | long | Minimum since last deactivation. |
| need_to_adjust_interval | long | Need to adjust interval. |
| new_session | long | New session. |
| next_predicted_resume_time | long | Next predicted resume time timestamp. |
| now_minutes | long | Now minutes. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| outcome | string | Outcome. |
| package | string | Package. |
| physical_database_guid | string | Physical database guid. |
| physical_pause_delay | long | Physical pause delay. |
| precondition_check_status | long | Status value for precondition check. |
| prev_outcome | string | Prev outcome. |
| previous_duration_min | long | Previous duration min. |
| previous_inactive_duration_min | long | Previous inactive duration min. |
| proactive_decision | string | Proactive decision. |
| reason | long | Reason. |
| rpc_request_type | string | Type classification for rpc request. |
| secondary_min_historyS | long | Secondary min history S. |
| server_name | string | Managed Instance server name. |
| sessionName | string | Session Name. |
| session_comparison | long | Session comparison. |
| session_historyS | long | Session history S. |
| session_id | string | Session identifier. |
| session_threshold | long | Session threshold. |
| size_comparison | long | Size comparison. |
| size_historyS | long | Size history S. |
| size_threshold | long | Size threshold. |
| slo_name | string | Slo name. |
| source | long | Source. |
| spinnaker_free_credits_remaining | long | Spinnaker free credits remaining. |
| start_of_predicted_activity | string | Start of predicted activity. |
| user_activity_detection_interval | long | User activity detection interval. |
| user_slo | string | User slo. |
| worker_comparison | long | Worker comparison. |
| worker_historyS | long | Worker history S. |
| worker_threshold | long | Worker threshold. |
| workflow_name | string | Workflow name. |

## MonGovernorResourcePools — Governor Resource Pools

**Purpose**: Governor Resource Pools. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| active_memgrant_count | long | Number of active memgrant. |
| active_memgrant_kb | long | Active memgrant kb. |
| active_session_count | long | Number of active session. |
| active_worker_count | long | Number of active worker. |
| cache_memory_kb | long | Cache memory kb. |
| cap_cpu_percent | long | Cap CPU percentage. |
| code_package_version | string | Code package version. |
| compile_memory_kb | long | Compile memory kb. |
| databasepages_memory_kb | long | Databasepages memory kb. |
| delta_active_memgrant_count | long | Number of delta active memgrant. |
| delta_active_memgrant_kb | long | Delta active memgrant kb. |
| delta_cache_memory_kb | long | Delta cache memory kb. |
| delta_compile_memory_kb | long | Delta compile memory kb. |
| delta_io_issue_delay_total_ms | long | Delta I/O issue delay total ms in milliseconds. |
| delta_io_issue_violations_total | long | Delta I/O issue violations total. |
| delta_is_valid | long | Delta is valid. |
| delta_memgrant_waiter_count | long | Number of delta memgrant waiter. |
| delta_out_of_memory_count | long | Number of delta out of memory. |
| delta_read_bytes_total | long | Delta read size in bytes total. |
| delta_read_io_completed_total | long | Delta read I/O completed total. |
| delta_read_io_issued_total | long | Delta read I/O issued total. |
| delta_read_io_queued_total | long | Delta read I/O queued total. |
| delta_read_io_stall_queued_ms | long | Delta read I/O stall queued ms in milliseconds. |
| delta_read_io_stall_total_ms | long | Delta read I/O stall total ms in milliseconds. |
| delta_read_io_throttled_total | long | Delta read I/O throttled total. |
| delta_total_cpu_usage_ms | long | Delta total CPU usage ms in milliseconds. |
| delta_total_cpu_usage_preemptive_ms | long | Delta total CPU usage preemptive ms in milliseconds. |
| delta_total_cpu_violation_delay_ms | long | Delta total CPU violation delay ms in milliseconds. |
| delta_total_cpu_violation_sec | long | Delta total CPU violation sec. |
| delta_total_memgrant_count | long | Number of delta total memgrant. |
| delta_total_memgrant_timeout_count | long | Number of delta total memgrant timeout. |
| delta_used_memgrant_kb | long | Delta used memgrant kb. |
| delta_used_memory_kb | long | Delta used memory kb. |
| delta_write_bytes_total | long | Delta write size in bytes total. |
| delta_write_io_completed_total | long | Delta write I/O completed total. |
| delta_write_io_issued_total | long | Delta write I/O issued total. |
| delta_write_io_queued_total | long | Delta write I/O queued total. |
| delta_write_io_stall_queued_ms | long | Delta write I/O stall queued ms in milliseconds. |
| delta_write_io_stall_total_ms | long | Delta write I/O stall total ms in milliseconds. |
| delta_write_io_throttled_total | long | Delta write I/O throttled total. |
| end_utc_date | datetime | End utc date. |
| govern_db_memory_in_resource_pool | long | Govern database memory in resource pool. |
| io_issue_ahead_total_ms | long | I/O issue ahead total ms in milliseconds. |
| io_issue_delay_non_throttled_total_ms | long | I/O issue delay non throttled total ms in milliseconds. |
| io_issue_delay_total_ms | long | I/O issue delay total ms in milliseconds. |
| io_issue_violations_total | long | I/O issue violations total. |
| log_bytes_used_total | long | Log size in bytes used total. |
| log_commit_fee | long | Log commit fee. |
| log_max_idle_credit | long | Log max idle credit. |
| log_rollback_factor | long | Log rollback factor. |
| max_cpu_percent | long | Maximum CPU percentage. |
| max_data_space_kb | long | Maximum data space kb. |
| max_iops_per_volume | long | Maximum IOPS per volume. |
| max_log_rate_bps | long | Maximum log rate bps. |
| max_memory_kb | long | Maximum memory kb. |
| max_memory_percent | real | Maximum memory percentage. |
| max_session_count | long | Number of max session. |
| memgrant_waiter_count | long | Number of memgrant waiter. |
| min_cpu_percent | long | Minimum CPU percentage. |
| min_iops_per_volume | long | Minimum IOPS per volume. |
| min_log_rate_bps | long | Minimum log rate bps. |
| min_memory_percent | real | Minimum memory percentage. |
| min_violation_cpu_sec | long | Minimum violation CPU sec. |
| name | string | Object or resource name. |
| out_of_memory_count | long | Number of out of memory. |
| peak_memory_kb | long | Peak memory kb. |
| pool_id | long | Pool identifier. |
| pool_max_workers | long | Pool max workers. |
| read_bytes_total | long | Read size in bytes total. |
| read_io_completed_total | long | Read I/O completed total. |
| read_io_issued_total | long | Read I/O issued total. |
| read_io_queued_total | long | Read I/O queued total. |
| read_io_stall_queued_ms | long | Read I/O stall queued ms in milliseconds. |
| read_io_stall_total_ms | long | Read I/O stall total ms in milliseconds. |
| read_io_throttled_total | long | Read I/O throttled total. |
| reserved_io_limited_by_volume_total | long | Reserved I/O limited by volume total. |
| start_utc_date | datetime | Start utc date. |
| statistics_start_time | datetime | Statistics start time timestamp. |
| target_memory_kb | long | Target memory kb. |
| target_memory_percent | real | Target memory percentage. |
| throttle_cpu_count | long | Number of throttle CPU. |
| total_cpu_active_ms | long | Total CPU active ms. |
| total_cpu_delayed_ms | long | Total CPU delayed ms. |
| total_cpu_usage_ms | long | Total CPU usage ms. |
| total_cpu_usage_preemptive_ms | long | Total CPU usage preemptive ms. |
| total_cpu_violation_delay_ms | long | Total CPU violation delay ms. |
| total_cpu_violation_sec | long | Total CPU violation sec. |
| total_memgrant_count | long | Number of total memgrant. |
| total_memgrant_timeout_count | long | Number of total memgrant timeout. |
| used_data_space_kb | long | Used data space kb. |
| used_memgrant_kb | long | Used memgrant kb. |
| used_memory_kb | long | Used memory kb. |
| write_bytes_total | long | Write size in bytes total. |
| write_io_completed_total | long | Write I/O completed total. |
| write_io_issued_total | long | Write I/O issued total. |
| write_io_queued_total | long | Write I/O queued total. |
| write_io_stall_queued_ms | long | Write I/O stall queued ms in milliseconds. |
| write_io_stall_total_ms | long | Write I/O stall total ms in milliseconds. |
| write_io_throttled_total | long | Write I/O throttled total. |

## MonGovernorWorkloadGroups — Governor Workload Groups

**Purpose**: Governor Workload Groups. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| active_parallel_thread_count | long | Number of active parallel thread. |
| active_request_count | long | Number of active request. |
| active_session_count | long | Number of active session. |
| active_worker_count | long | Number of active worker. |
| alternate_io_factor | long | Alternate I/O factor. |
| avg_read_iops | long | Average read IOPS. |
| avg_write_iops | long | Average write IOPS. |
| background_write_bytes_total | long | Background write size in bytes total. |
| background_writes_total | long | Background writes total. |
| blocked_task_count | long | Number of blocked task. |
| bucket_cap_cpu_percent | real | Bucket cap CPU percentage. |
| bucket_depth_cpu_ms | long | Bucket depth CPU ms in milliseconds. |
| bucket_fill_rate_cpu_ms | long | Bucket fill rate CPU ms in milliseconds. |
| bucket_min_cpu_percent | real | Bucket min CPU percentage. |
| cap_cpu_percent | real | Cap CPU percentage. |
| checkpoint_page_limit | long | Checkpoint page limit. |
| code_package_version | string | Code package version. |
| database_name | string | Database name. |
| delta_background_write_bytes_total | long | Delta background write size in bytes total. |
| delta_background_writes_total | long | Delta background writes total. |
| delta_io_active_time_ms | long | Delta I/O active time ms in milliseconds. |
| delta_io_issue_ahead_total_ms | long | Delta I/O issue ahead total ms in milliseconds. |
| delta_io_issue_delay_non_throttled_total_ms | long | Delta I/O issue delay non throttled total ms in milliseconds. |
| delta_io_issue_delay_total_ms | long | Delta I/O issue delay total ms in milliseconds. |
| delta_io_issue_violations_total | long | Delta I/O issue violations total. |
| delta_io_queue_limit_wait_total_ms | long | Delta I/O queue limit wait total ms in milliseconds. |
| delta_io_queue_limit_waits_total | long | Delta I/O queue limit waits total. |
| delta_is_valid | long | Delta is valid. |
| delta_log_bytes_allotted_total | long | Delta log size in bytes allotted total. |
| delta_log_bytes_overhead_total | long | Delta log size in bytes overhead total. |
| delta_log_bytes_used_total | long | Delta log size in bytes used total. |
| delta_log_commits_tracked_total | long | Delta log commits tracked total. |
| delta_log_operations_tracked_total | long | Delta log operations tracked total. |
| delta_log_temp_db_bytes_used_total | long | Delta log temp database size in bytes used total. |
| delta_log_time_waited_for_allotment_total_ms | long | Delta log time waited for allotment total ms in milliseconds. |
| delta_log_waits_for_allotment_total | long | Delta log waits for allotment total. |
| delta_normalized_reads_completed_total | long | Delta normalized reads completed total. |
| delta_normalized_reads_issued_total | long | Delta normalized reads issued total. |
| delta_normalized_reads_throttled_total | long | Delta normalized reads throttled total. |
| delta_normalized_writes_completed_total | long | Delta normalized writes completed total. |
| delta_normalized_writes_issued_total | long | Delta normalized writes issued total. |
| delta_normalized_writes_throttled_total | long | Delta normalized writes throttled total. |
| delta_read_ahead_pages_total | long | Delta read ahead pages total. |
| delta_read_ahead_total | long | Delta read ahead total. |
| delta_read_bytes_total | long | Delta read size in bytes total. |
| delta_read_stall_queued_ms | long | Delta read stall queued ms in milliseconds. |
| delta_read_stall_total_ms | long | Delta read stall total ms in milliseconds. |
| delta_reads_completed_total | long | Delta reads completed total. |
| delta_reads_issued_total | long | Delta reads issued total. |
| delta_reads_queued_total | long | Delta reads queued total. |
| delta_reads_throttled_total | long | Delta reads throttled total. |
| delta_reserved_io_limited_by_volume_total | long | Delta reserved I/O limited by volume total. |
| delta_slo_violations_cpu_count | long | Number of delta slo violations CPU. |
| delta_slo_violations_cpu_deficit_ms | long | Delta slo violations CPU deficit ms in milliseconds. |
| delta_slo_violations_io_count | long | Number of delta slo violations I/O. |
| delta_slo_violations_io_deficit_ios | long | Delta slo violations I/O deficit ios. |
| delta_slo_violations_log_count | long | Number of delta slo violations log. |
| delta_slo_violations_log_deficit_bytes | long | Delta slo violations log deficit size in bytes. |
| delta_slo_violations_total_count | long | Number of delta slo violations total. |
| delta_total_cpu_active_ms | long | Delta total CPU active ms in milliseconds. |
| delta_total_cpu_delayed_ms | long | Delta total CPU delayed ms in milliseconds. |
| delta_total_cpu_limit_violation_count | long | Number of delta total CPU limit violation. |
| delta_total_cpu_usage_ms | long | Delta total CPU usage ms in milliseconds. |
| delta_total_cpu_usage_preemptive_ms | long | Delta total CPU usage preemptive ms in milliseconds. |
| delta_total_cpu_violation_delay_ms | long | Delta total CPU violation delay ms in milliseconds. |
| delta_total_cpu_violation_sec | long | Delta total CPU violation sec. |
| delta_total_lock_wait_count | long | Number of delta total lock wait. |
| delta_total_lock_wait_time_ms | long | Delta total lock wait time ms in milliseconds. |
| delta_total_query_optimization_count | long | Number of delta total query optimization. |
| delta_total_queued_request_count | long | Number of delta total queued request. |
| delta_total_reduced_memgrant_count | long | Number of delta total reduced memgrant. |
| delta_total_request_count | long | Number of delta total request. |
| delta_total_suboptimal_plan_generation_count | long | Number of delta total suboptimal plan generation. |
| delta_write_bytes_total | long | Delta write size in bytes total. |
| delta_write_stall_queued_ms | long | Delta write stall queued ms in milliseconds. |
| delta_write_stall_total_ms | long | Delta write stall total ms in milliseconds. |
| delta_writes_completed_total | long | Delta writes completed total. |
| delta_writes_issued_total | long | Delta writes issued total. |
| delta_writes_queued_total | long | Delta writes queued total. |
| delta_writes_throttled_total | long | Delta writes throttled total. |
| effective_max_dop | long | Effective max dop. |
| end_utc_date | datetime | End utc date. |
| external_pool_id | long | External pool identifier. |
| govern_background_io | long | Govern background I/O. |
| group_id | long | Group identifier. |
| group_max_requests | long | Group max requests. |
| group_max_sessions | long | Group max sessions. |
| group_max_workers | long | Group max workers. |
| group_min_memory_kb | long | Group min memory kb. |
| group_min_memory_percent | long | Group min memory percentage. |
| importance | string | Importance. |
| io_active_time_ms | long | I/O active time ms in milliseconds. |
| io_issue_ahead_total_ms | long | I/O issue ahead total ms in milliseconds. |
| io_issue_delay_non_throttled_total_ms | long | I/O issue delay non throttled total ms in milliseconds. |
| io_issue_delay_total_ms | long | I/O issue delay total ms in milliseconds. |
| io_issue_violations_total | long | I/O issue violations total. |
| io_queue_limit_wait_total_ms | long | I/O queue limit wait total ms in milliseconds. |
| io_queue_limit_waits_total | long | I/O queue limit waits total. |
| log_bytes_allotted_total | long | Log size in bytes allotted total. |
| log_bytes_balance | long | Log size in bytes balance. |
| log_bytes_overhead_total | long | Log size in bytes overhead total. |
| log_bytes_used_last_sec | long | Log size in bytes used last sec. |
| log_bytes_used_total | long | Log size in bytes used total. |
| log_commit_fee | long | Log commit fee. |
| log_commits_tracked_last_sec | long | Log commits tracked last sec. |
| log_commits_tracked_total | long | Log commits tracked total. |
| log_flush_time_total_ms | long | Log flush time total ms in milliseconds. |
| log_flushes | long | Log flushes. |
| log_max_idle_credit | long | Log max idle credit. |
| log_operations_tracked_total | long | Log operations tracked total. |
| log_rollback_factor | long | Log rollback factor. |
| log_temp_db_byte_factor | real | Log temp database byte factor. |
| log_temp_db_bytes_used_total | long | Log temp database size in bytes used total. |
| log_time_user_active_total_ms | long | Log time user active total ms in milliseconds. |
| log_time_user_idle_total_ms | long | Log time user idle total ms in milliseconds. |
| log_time_waited_for_allotment_total_ms | long | Log time waited for allotment total ms in milliseconds. |
| log_waits_for_allotment_total | long | Log waits for allotment total. |
| max_cpu_percent | real | Maximum CPU percentage. |
| max_databasepages_kb | long | Maximum databasepages kb. |
| max_dop | long | Maximum dop. |
| max_global_io | long | Maximum global I/O. |
| max_idle_credit_io | long | Maximum idle credit I/O. |
| max_io | long | Maximum I/O. |
| max_log_rate | long | Maximum log rate. |
| max_request_cpu_time_ms | long | Maximum request CPU time ms. |
| max_request_grant_memory_kb | long | Maximum request grant memory kb. |
| max_transaction_size | long | Maximum transaction size. |
| min_cpu_percent | real | Minimum CPU percentage. |
| min_global_io | long | Minimum global I/O. |
| min_io | long | Minimum I/O. |
| min_log_rate | long | Minimum log rate. |
| name | string | Object or resource name. |
| normalized_reads_completed_total | long | Normalized reads completed total. |
| normalized_reads_issued_total | long | Normalized reads issued total. |
| normalized_reads_throttled_total | long | Normalized reads throttled total. |
| normalized_writes_completed_total | long | Normalized writes completed total. |
| normalized_writes_issued_total | long | Normalized writes issued total. |
| normalized_writes_throttled_total | long | Normalized writes throttled total. |
| peak_memory_kb | long | Peak memory kb. |
| peak_session_count | long | Number of peak session. |
| peak_worker_count | long | Number of peak worker. |
| pool_id | long | Pool identifier. |
| queue_limit_io | long | Queue limit I/O. |
| queued_request_count | long | Number of queued request. |
| read_ahead_pages_total | long | Read ahead pages total. |
| read_ahead_total | long | Read ahead total. |
| read_bytes_total | long | Read size in bytes total. |
| read_stall_queued_ms | long | Read stall queued ms in milliseconds. |
| read_stall_total_ms | long | Read stall total ms in milliseconds. |
| reads_completed_last_sec | long | Reads completed last sec. |
| reads_completed_total | long | Reads completed total. |
| reads_issued_last_sec | long | Reads issued last sec. |
| reads_issued_total | long | Reads issued total. |
| reads_queued_last_sec | long | Reads queued last sec. |
| reads_queued_total | long | Reads queued total. |
| reads_throttled_total | long | Reads throttled total. |
| request_max_cpu_time_sec | long | Request max CPU time sec. |
| request_max_memory_grant_percent | real | Request max memory grant percentage. |
| request_memory_grant_timeout_sec | long | Request memory grant timeout sec. |
| reserved_io_limited_by_volume_total | long | Reserved I/O limited by volume total. |
| server_name | string | Managed Instance server name. |
| slo_violations_cpu_count | long | Number of slo violations CPU. |
| slo_violations_cpu_deficit_ms | long | Slo violations CPU deficit ms in milliseconds. |
| slo_violations_io_count | long | Number of slo violations I/O. |
| slo_violations_io_deficit_ios | long | Slo violations I/O deficit ios. |
| slo_violations_log_count | long | Number of slo violations log. |
| slo_violations_log_deficit_bytes | long | Slo violations log deficit size in bytes. |
| slo_violations_total_count | long | Number of slo violations total. |
| start_utc_date | datetime | Start utc date. |
| statistics_start_time | datetime | Statistics start time timestamp. |
| token_bucket_depth_io | long | Token bucket depth I/O. |
| token_bucket_fill_rate_io | long | Token bucket fill rate I/O. |
| token_bucket_max_io | long | Token bucket max I/O. |
| token_bucket_min_io | long | Token bucket min I/O. |
| total_cpu_active_ms | long | Total CPU active ms. |
| total_cpu_delayed_ms | long | Total CPU delayed ms. |
| total_cpu_idle_capped_by_instance_cap_ms | long | Total CPU idle capped by instance cap ms. |
| total_cpu_idle_capped_ms | long | Total CPU idle capped ms. |
| total_cpu_limit_violation_count | long | Number of total CPU limit violation. |
| total_cpu_usage_ms | long | Total CPU usage ms. |
| total_cpu_usage_preemptive_ms | long | Total CPU usage preemptive ms. |
| total_cpu_violation_delay_ms | long | Total CPU violation delay ms. |
| total_cpu_violation_sec | long | Total CPU violation sec. |
| total_lock_wait_count | long | Number of total lock wait. |
| total_lock_wait_time_ms | long | Total lock wait time ms. |
| total_query_optimization_count | long | Number of total query optimization. |
| total_queued_request_count | long | Number of total queued request. |
| total_reduced_memgrant_count | long | Number of total reduced memgrant. |
| total_request_count | long | Number of total request. |
| total_suboptimal_plan_generation_count | long | Number of total suboptimal plan generation. |
| used_databasepages_kb | long | Used databasepages kb. |
| used_memory_kb | long | Used memory kb. |
| write_bytes_total | long | Write size in bytes total. |
| write_stall_queued_ms | long | Write stall queued ms in milliseconds. |
| write_stall_total_ms | long | Write stall total ms in milliseconds. |
| writes_completed_last_sec | long | Writes completed last sec. |
| writes_completed_total | long | Writes completed total. |
| writes_issued_last_sec | long | Writes issued last sec. |
| writes_issued_total | long | Writes issued total. |
| writes_queued_last_sec | long | Writes queued last sec. |
| writes_queued_total | long | Writes queued total. |
| writes_throttled_total | long | Writes throttled total. |

## MonManagedInstanceResourceStats — Instance-level resource utilization

**Purpose**: Instance-level resource utilization. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: availability, backup-restore, performance. Often used during backup or restore investigations.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| ResourcePoolName | string | Resource Pool Name. |
| active_sessions | long | Active sessions. |
| active_sessions_percent | real | Active sessions percentage. |
| active_workers | long | Active workers. |
| active_workers_percent | real | Active workers percentage. |
| actual_interval_ms | long | Actual interval ms in milliseconds. |
| avg_cpu_percent | real | Average CPU utilization percentage. |
| avg_job_object_cpu_percent | real | Average job object CPU percentage. |
| avg_job_object_memory_percent | real | Average job object memory percentage. |
| avg_log_write_percent | real | Average log write utilization percentage. |
| avg_logins_percent | real | Average logins percentage. |
| backup_storage_consumption_mb | real | Backup storage consumption mb. |
| code_package_version | string | Code package version. |
| core_count | long | Number of core. |
| cpu_cap_ms | real | CPU cap ms in milliseconds. |
| cpu_cap_per_second | real | CPU cap per second. |
| cpu_time_ms | long | CPU time ms in milliseconds. |
| desired_interval_ms | long | Desired interval ms in milliseconds. |
| end_time | datetime | End timestamp. |
| event | string | Event name emitted by the component. |
| hardware_generation | string | Hardware generation. |
| io_bytes_read | long | I/O size in bytes read. |
| io_bytes_written | long | I/O size in bytes written. |
| io_requests | long | I/O requests. |
| log_bytes_used_total | long | Log size in bytes used total. |
| node_memory_percent | real | Node memory percentage. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| reserved_storage_iops | long | Reserved storage IOPS. |
| reserved_storage_mb | long | Reserved storage mb. |
| scheduler_count | real | Number of scheduler. |
| server_name | string | Managed Instance server name. |
| sessionName | string | Session Name. |
| sku | string | Sku. |
| start_time | datetime | Start timestamp. |
| storage_space_used_mb | real | Storage space used mb. |
| total_cpu_usage_ms | long | Total CPU usage ms. |
| total_logins | long | Total logins. |
| virtual_core_count | long | Number of virtual core. |

## MonResourcePoolStats — Resource Pool Stats

**Purpose**: Resource Pool Stats. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| allocated_data_storage_percent | real | Allocated data storage percentage. |
| attach_activity_id | string | Attach activity identifier. |
| attach_activity_id_xfer | string | Attach activity id xfer. |
| avg_cpu_percent | real | Average CPU utilization percentage. |
| avg_data_io_percent | real | Average data I/O utilization percentage. |
| avg_instance_cpu_percent | real | Average instance CPU percentage. |
| avg_instance_memory_percent | real | Average instance memory percentage. |
| avg_log_write_percent | real | Average log write utilization percentage. |
| avg_login_rate_percent | real | Average login rate percentage. |
| avg_memory_usage_percent | real | Average memory utilization percentage. |
| data_storage_percent | real | Data storage percentage. |
| end_time | datetime | End timestamp. |
| event | string | Event name emitted by the component. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| peak_session_percent | real | Peak session percentage. |
| peak_worker_percent | real | Peak worker percentage. |
| peak_xtp_storage_percent | real | Peak In-Memory OLTP storage percentage. |
| resource_pool_cpu_limit | real | Resource pool CPU limit. |
| resource_pool_dtu_limit | string | Resource pool dtu limit. |
| resource_pool_name | string | Resource pool name. |
| resource_pool_storage_limit | string | Resource pool storage limit. |
| server_name | string | Managed Instance server name. |
| sessionName | string | Session Name. |
| start_time | datetime | Start timestamp. |

## MonRgLoad — resource governor Load

**Purpose**: resource governor Load. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: availability, backup-restore, networking, performance. Often used during backup or restore investigations.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| allocated_cpus | string | Allocated cpus. |
| app_cpu_current_cap | real | App CPU current cap. |
| app_cpu_load | real | App CPU load. |
| app_cpu_load_cap | real | App CPU load cap. |
| app_cpu_load_cap_normalized | real | App CPU load cap normalized. |
| app_cpu_load_normalized | real | App CPU load normalized. |
| app_cpu_load_normalized_peak | real | App CPU load normalized peak. |
| app_cpu_load_peak | real | App CPU load peak. |
| app_cpu_metric_average | real | App CPU metric average. |
| app_cpu_metric_average_peak | real | App CPU metric average peak. |
| app_iops_load | real | App IOPS load. |
| app_iops_load_cap | real | App IOPS load cap. |
| app_iops_load_peak | real | App IOPS load peak. |
| app_kernel_load | real | App kernel load. |
| app_kernel_load_peak | real | App kernel load peak. |
| app_memory_current_cap | real | App memory current cap. |
| app_memory_load | real | App memory load. |
| app_memory_load_cap | real | App memory load cap. |
| app_memory_load_cap_normalized | real | App memory load cap normalized. |
| app_memory_load_normalized | real | App memory load normalized. |
| app_memory_load_normalized_peak | real | App memory load normalized peak. |
| app_memory_load_peak | real | App memory load peak. |
| app_memory_metric_average | real | App memory metric average. |
| app_memory_metric_average_peak | real | App memory metric average peak. |
| app_network_application_ports_used | long | App network application ports used. |
| app_network_ephemeral_ports_used | long | App network ephemeral ports used. |
| app_network_port_used | long | App network port used. |
| app_network_receive_mbps | real | App network receive mbps. |
| app_network_send_mbps | real | App network send mbps. |
| app_working_set_load | real | App working set load. |
| app_working_set_load_cap | real | App working set load cap. |
| app_working_set_memory_metric_average | real | App working set memory metric average. |
| app_working_set_memory_metric_peak | real | App working set memory metric peak. |
| app_working_set_peak | real | App working set peak. |
| application_correlation_id | long | Application correlation identifier. |
| application_name | string | Application name. |
| application_type | string | Type classification for application. |
| are_physical_cpus_allocated | string | Are physical cpus allocated. |
| attach_activity_id | string | Attach activity identifier. |
| attach_activity_id_xfer | string | Attach activity id xfer. |
| boosted_state | string | State value for boosted. |
| clr_app_domain_name | string | Clr app domain name. |
| code_package_name | string | Code package name. |
| code_package_start_time | long | Code package start time timestamp. |
| code_package_version | string | Code package version. |
| cpu_count | long | Number of CPU. |
| cpu_current_cap | real | CPU current cap. |
| cpu_load | real | CPU load. |
| cpu_load_cap | real | CPU load cap. |
| cpu_load_peak | real | CPU load peak. |
| cpu_total_load_cap | string | CPU total load cap. |
| database_name | string | Database name. |
| database_size_mb | long | Database size mb. |
| drive_capacity_in_bytes | long | Drive capacity in size in bytes. |
| drive_guid | string | Drive guid. |
| drive_name | string | Drive name. |
| drive_usage_alert_threshold_percentage | real | Drive usage alert threshold pe percentage. |
| drive_usage_percentage | real | Drive usage pe percentage. |
| event | string | Event name emitted by the component. |
| full_node_application_name | string | Full node application name. |
| global_cpu_cap | real | Global CPU cap. |
| guest_os_version | string | Guest OS version. |
| has_full_node_app | bool | Boolean flag indicating whether has full node app. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| instance_analytical_service_type | string | Type classification for instance analytical service. |
| instance_datawarehouse_name | string | Instance datawarehouse name. |
| instance_logical_server_name | string | Instance logical server name. |
| instance_resource_group | string | Instance resource group. |
| instance_subscription_id | string | Instance subscription identifier. |
| instance_target_logical_guid | string | Instance target logical guid. |
| instance_target_name | string | Instance target name. |
| instance_workspace_resource_group_name | string | Instance workspace resource group name. |
| io_settings_for_volumes | string | I/O settings for volumes. |
| iops_load | real | IOPS load. |
| iops_load_cap | real | IOPS load cap. |
| iops_load_peak | real | IOPS load peak. |
| is_fake_metric | string | Boolean flag indicating whether fake metric. |
| is_isolated | bool | Boolean flag indicating whether isolated. |
| is_logical_basis | bool | Boolean flag indicating whether logical basis. |
| is_pool | bool | Boolean flag indicating whether pool. |
| is_quota_hard | bool | Boolean flag indicating whether quota hard. |
| is_zone_resilient | bool | Boolean flag indicating whether zone resilient. |
| job_name | string | Job name. |
| json_explanation | string | Json explanation. |
| kernel_load | real | Kernel load. |
| kernel_load_peak | real | Kernel load peak. |
| max_allowed_violated_cores | real | Maximum allowed violated cores. |
| max_logical_cores | long | Maximum logical cores. |
| mdsReserved | bool | Boolean flag indicating whether mds Reserved. |
| mdsReservedRg | bool | Boolean flag indicating whether mds Reserved resource governor. |
| mdsReservedRgDW | bool | Boolean flag indicating whether mds Reserved resource governor billing warehouse. |
| mdsReservedRgSynapse | bool | Boolean flag indicating whether mds Reserved resource governor Synapse. |
| mdsReservedTps | bool | Boolean flag indicating whether mds Reserved Tps. |
| memory_current_cap | real | Memory current cap. |
| memory_lgc_app_domain_load | real | Memory lgc app domain load. |
| memory_lgc_app_domain_load_peak | real | Memory lgc app domain load peak. |
| memory_lgc_application_load | real | Memory lgc application load. |
| memory_lgc_application_load_peak | real | Memory lgc application load peak. |
| memory_load | real | Memory load. |
| memory_load_cap | real | Memory load cap. |
| memory_load_peak | long | Memory load peak. |
| memory_total_allocation_load | real | Memory total allocation load. |
| memory_total_allocation_load_peak | real | Memory total allocation load peak. |
| metric_name | string | Metric name. |
| metric_value | long | Metric value. |
| metric_value_peak | long | Metric value peak. |
| move_cost | long | Move cost. |
| node_avg_system_cpu_usage | real | Node avg system CPU usage. |
| node_avg_user_cpu_usage | real | Node avg user CPU usage. |
| node_capacity | long | Node capacity. |
| node_physical_mem_mb | string | Node physical memory mb. |
| node_physical_usage_mb | long | Node physical usage mb. |
| node_sku | string | Node sku. |
| node_system_cpu_usage | real | Node system CPU usage. |
| node_total_commit_mem_mb | string | Node total commit memory mb. |
| node_used_capacity | real | Node used capacity. |
| node_used_commit_mem_mb | string | Node used commit memory mb. |
| node_user_cpu_allocation | long | Node user CPU allocation. |
| node_user_cpu_usage | real | Node user CPU usage. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| originalEventTimestampFrom | datetime | Original Event Timestamp From. |
| originalEventTimestampTo | datetime | Original Event Timestamp To. |
| other_iops | real | Other IOPS. |
| other_mbps | real | Other mbps. |
| package | string | Package. |
| partition_id | string | Partition identifier. |
| peak_memory_load | real | Peak memory load. |
| peak_quota_usage_in_bytes | long | Peak quota usage in size in bytes. |
| peak_working_set_load | real | Peak working set load. |
| precise_metric_value | long | Precise metric value. |
| process_id | long | Process identifier. |
| process_name | string | Process name. |
| quota_limit_in_bytes | long | Quota limit in size in bytes. |
| quota_usage_alert_threshold_in_bytes | long | Quota usage alert threshold in size in bytes. |
| quota_usage_in_bytes | long | Quota usage in size in bytes. |
| quota_usage_in_bytes_peak | long | Quota usage in size in bytes peak. |
| read_iops | real | Read IOPS. |
| read_mbps | real | Read mbps. |
| replica_type | long | Type classification for replica. |
| result | long | Result. |
| result_desc | string | Result desc. |
| rg_instance_process_id | long | Resource governor instance process identifier. |
| serverless_billing_enabled | bool | Boolean flag indicating whether serverless billing enabled. |
| serverless_min_cpu | long | Serverless min CPU. |
| serverless_usage_reset_needed | bool | Boolean flag indicating whether serverless usage reset needed. |
| service_manifest_name | string | Service manifest name. |
| sessionName | string | Session Name. |
| slo_size | string | Slo size. |
| soft_cpu_rate | string | Soft CPU rate. |
| source | long | Source. |
| system_thread_id | long | System thread identifier. |
| target_directory | string | Target directory. |
| target_file_name | string | Target file name. |
| target_file_size_in_bytes | long | Target file size in size in bytes. |
| top_monitored_directory | string | Top monitored directory. |
| tr_overbooking_ratio | long | Tr overbooking ratio. |
| working_set_load | real | Working set load. |
| working_set_load_cap | real | Working set load cap. |
| working_set_load_peak | long | Working set load peak. |
| write_iops | real | Write IOPS. |
| write_mbps | real | Write mbps. |

## MonRgManager — resource governor Manager

**Purpose**: resource governor Manager. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: availability, backup-restore, performance. Often used during backup or restore investigations.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| CpuRateCap | long | CPU Rate Cap. |
| Level | long | Level. |
| MemCapInMB | long | Memory Cap In MB. |
| Name | string | Object or resource name. |
| OneBoxClusterId | string | One Box Cluster Id. |
| PartitionId | string | Partition Id. |
| Pid | long | Pid. |
| RegistryKeyName | string | Registry Key Name. |
| SystemMask | long | System Mask. |
| Tid | long | Tid. |
| Timestamp | string | timestamp. |
| _name | string | Name. |
| action_name | string | Action name. |
| action_type | string | Type classification for action. |
| actions | string | Actions. |
| actual_aux_replica_ratio | real | Actual aux replica ratio. |
| adjust_metric_value | long | Adjust metric value. |
| affinity_type | long | Type classification for affinity. |
| aggregate_node_usage | real | Aggregate node usage. |
| allocated_cpus | string | Allocated cpus. |
| allocated_cpus_job_object | long | Allocated cpus job object. |
| allocation | string | Allocation. |
| amu_snapshot | string | Amu snapshot. |
| amu_view_type | long | Type classification for amu view. |
| app_count | long | Number of app. |
| app_cpu_usage | long | App CPU usage. |
| app_memory_usage_mb | long | App memory usage mb. |
| app_module | string | App module. |
| app_overbooking_ratio | long | App overbooking ratio. |
| app_path | string | App path. |
| app_total_used | long | App total used. |
| application_affinity | string | Application affinity. |
| application_correlation_id | long | Application correlation identifier. |
| application_cpu_allocation_group | string | Application CPU allocation group. |
| application_directory | string | Application directory. |
| application_name | string | Application name. |
| application_state | long | State value for application. |
| application_type | string | Type classification for application. |
| apply_high_pm | string | Apply high pm. |
| apply_low_pm | string | Apply low pm. |
| are_cpu_groups_enabled | bool | Boolean flag indicating whether are CPU groups enabled. |
| are_physical_cpus_allocated | bool | Boolean flag indicating whether are physical cpus allocated. |
| arguments | string | Arguments. |
| async_action_timeout_ms | long | Async action timeout ms in milliseconds. |
| attach_activity_id | string | Attach activity identifier. |
| attach_activity_id_xfer | string | Attach activity id xfer. |
| authorize_app_duration | long | Authorize app duration. |
| auto_default_content | string | Auto default content. |
| auxiliary_replica_ratio | long | Auxiliary replica ratio. |
| available_capacity | real | Available capacity. |
| available_data_quota_in_bytes | long | Available data quota in size in bytes. |
| available_disk_space_in_bytes | long | Available disk space in size in bytes. |
| available_extended_virtual_address_space_kb | long | Available extended virtual address space kb. |
| available_memory_free_block_emergency_descriptors | long | Available memory free block emergency descriptors. |
| available_page_file_kb | long | Available page file kb. |
| available_physical_memory_kb | long | Available physical memory kb. |
| available_virtual_address_space_kb | long | Available virtual address space kb. |
| average_time_spent_waiting_ms | long | Average time spent waiting ms in milliseconds. |
| average_write_latency_ms | long | Average write latency ms in milliseconds. |
| average_write_throughput_mbps | long | Average write throughput mbps. |
| avg_execution_time_ms | long | Average execution time ms. |
| avg_percent_dpc_time | real | Avg percentage dpc time timestamp. |
| avg_queue_time_ms | long | Average queue time ms. |
| avg_time_ms | long | Average time ms. |
| avg_wait_time_ms | long | Average wait time ms. |
| awe_kb | long | Awe kb. |
| azure_profiler_flavor | long | Azure profiler flavor. |
| azure_profiler_mode | long | Azure profiler mode. |
| body | string | Body. |
| bool_value | bool | Boolean flag indicating whether bool value. |
| boosted_state | string | State value for boosted. |
| buffer_space_mb | long | Buffer space mb. |
| calculation_duration_us | long | Calculation duration us. |
| call_stack | string | Call stack. |
| cap_name | string | Cap name. |
| cap_value | string | Cap value. |
| capacity_usage | long | Capacity usage. |
| capped_value | real | Capped value. |
| child_process_id | long | Child process identifier. |
| chunk_size_mb | long | Chunk size mb. |
| client_execution_env | long | Client execution env. |
| client_process_id | long | Client process identifier. |
| clr_application_configuration_path | string | Clr application configuration path. |
| clr_application_name | string | Clr application name. |
| clr_application_path | string | Clr application path. |
| clr_runtime_version | string | Clr runtime version. |
| code_package_name | string | Code package name. |
| code_package_start_time | long | Code package start time timestamp. |
| code_package_version | string | Code package version. |
| cold_node_window | long | Cold node window. |
| cold_time_window | long | Cold time window. |
| collect_current_thread_id | long | Collect current thread identifier. |
| command_line | string | Command line. |
| committed_kb | long | Committed kb. |
| committed_mem_usage_percent | real | Committed memory usage percentage. |
| config_name | string | Config name. |
| config_or_property_name | string | Config or property name. |
| config_value | string | Config value. |
| connection_id | string | Connection identifier. |
| consecutive_detection | long | Consecutive detection. |
| convert_to | string | Convert to. |
| count | long | Number of count. |
| counter_name | string | Counter name. |
| cpu_core_usage | string | CPU core usage. |
| cpu_count | long | Number of CPU. |
| cpu_load | long | CPU load. |
| cpu_manager_state | string | State value for CPU manager. |
| cpu_manager_total_cpu | long | CPU manager total CPU. |
| cpu_percent | long | CPU percentage. |
| cpu_rate | long | CPU rate. |
| cpu_rate_job_object | long | CPU rate job object. |
| cpugroup_durationMillis | long | Cpugroup duration Millis. |
| creation_time | long | Creation time timestamp. |
| criteria | string | Criteria. |
| ctrl_type | long | Type classification for ctrl. |
| current_cpu_cap | long | Current CPU cap. |
| current_cpu_percentage | long | Current CPU pe percentage. |
| current_memory_cap | long | Current memory cap. |
| current_node_usage | real | Current node usage. |
| current_slo_cap | real | Current slo cap. |
| cut_off | long | Cut off. |
| data_written_mb | long | Data written mb. |
| database_name | string | Database name. |
| database_size_mb | long | Database size mb. |
| default_group_affinity | string | Default group affinity. |
| default_move_cost | long | Default move cost. |
| delta_amu_inflation_amount_due_to_commit_pressure | long | Delta amu inflation amount due to commit pressure. |
| delta_reduction_for_vhmc | long | Delta reduction for vhmc. |
| deployment_status | long | Status value for deployment. |
| description | string | Description. |
| description_prefix | string | Description prefix. |
| difference_between_min_and_max | long | Difference between min and max. |
| differential_overbooking_ratio | long | Differential overbooking ratio. |
| differential_sellable_ratio | long | Differential sellable ratio. |
| diffsmcu_value | long | Diffsmcu value. |
| disk_capacity_mb | long | Disk capacity mb. |
| disk_used_gb | real | Disk used gb. |
| disk_utilization_mb | long | Disk utilization mb. |
| dll_path | string | Dll path. |
| drive_used_space | long | Drive used space. |
| driver_desc | string | Driver desc. |
| duration | long | Duration. |
| durationMillis | long | Duration Millis. |
| enable_shortened_window | bool | Boolean flag indicating whether enable shortened window. |
| enable_snapshot | bool | Boolean flag indicating whether enable snapshot. |
| enable_time_sync | bool | Boolean flag indicating whether enable time sync. |
| end_state | long | State value for end. |
| enroll_mem_dynamic_rg | string | Enroll memory dynamic resource governor. |
| error | long | Error text captured for the event or operation. |
| error_code | long | Numeric error code for the failure or event. |
| error_log | string | Error log. |
| error_message | string | Error message. |
| error_number | long | SQL or platform error number. |
| errors_occurred | bool | Boolean flag indicating whether errors occurred. |
| estimated_time_remaining_ms | long | Estimated time remaining ms in milliseconds. |
| etw_memory_usage_mb | real | ETW memory usage mb. |
| etw_process_id | long | ETW process identifier. |
| etw_process_name | string | ETW process name. |
| event | string | Event name emitted by the component. |
| event_non_sf_governance | long | Event non sf governance. |
| event_type | string | Type classification for event. |
| exception | string | Exception. |
| exception_hash | long | Exception hash. |
| exit_code | long | Exit code. |
| expiry_time | datetime | Expiry time timestamp. |
| extra_param | string | Extra param. |
| fabric_deployment_status | string | Status value for fabric deployment. |
| fabric_partition_id | string | Fabric partition identifier. |
| failed_to_set_hard_quota | bool | Boolean flag indicating whether failed to set hard quota. |
| failure_ignored | bool | Boolean flag indicating whether failure ignored. |
| feature_name | string | Feature name. |
| feature_source | string | Feature source. |
| feature_state | bool | Boolean flag indicating whether feature state. |
| file_last_write_time | datetime | File last write time timestamp. |
| file_name | string | File name. |
| file_path | string | File path. |
| file_size | long | File size. |
| file_size_in_bytes | long | File size in size in bytes. |
| file_size_mb | long | File size mb. |
| file_spared | bool | Boolean flag indicating whether file spared. |
| follow_symlinks | bool | Boolean flag indicating whether follow symlinks. |
| full_node_app_name | string | Full node app name. |
| full_node_application_name | string | Full node application name. |
| function_name | string | Function name. |
| generic_diff_multi_instance_mem_rg_is_enabled | bool | Boolean flag indicating whether generic diff multi instance memory resource governor enabled. |
| get_app_type_duration | long | Get app type duration. |
| get_correct_replica_duration | long | Get correct replica duration. |
| get_slo_size_duration | long | Get slo size duration. |
| graceful | bool | Boolean flag indicating whether graceful. |
| gray_zone_window | long | Gray zone window. |
| grayzone_time_window | long | Grayzone time window. |
| group | string | Group. |
| group_indicators | long | Group indicators. |
| groups | string | Groups. |
| growth_file_path | string | Growth file path. |
| growth_file_size_mb | long | Growth file size mb. |
| has_full_node_app | bool | Boolean flag indicating whether has full node app. |
| health_report_raised | bool | Boolean flag indicating whether health report raised. |
| health_state | string | State value for health. |
| hot_node_window | long | Hot node window. |
| hot_time_window | long | Hot time window. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| hresult | long | Hresult. |
| hyper_threading_ratio | long | Hyper threading ratio. |
| id | long | identifier. |
| ignore_idsu_capacity | bool | Boolean flag indicating whether ignore idsu capacity. |
| imbalance_duration_mins | long | Imbalance duration mins. |
| imbalance_reason | string | Imbalance reason. |
| inactive_duration_in_min | long | Inactive duration in min. |
| input_cpus | string | Input cpus. |
| instance_datawarehouse_name | string | Instance datawarehouse name. |
| instance_logical_server_name | string | Instance logical server name. |
| instance_name | string | Instance name. |
| instance_replica_type | long | Type classification for instance replica. |
| instance_resource_group | string | Instance resource group. |
| instance_subscription_id | string | Instance subscription identifier. |
| instance_target_logical_guid | string | Instance target logical guid. |
| instance_target_name | string | Instance target name. |
| instance_user_slo_size | string | Instance user slo size. |
| interval_timeout_seconds | long | Interval timeout seconds. |
| invalid_id_as_zombie_enabled | bool | Boolean flag indicating whether invalid id as zombie enabled. |
| is_additive_deltaACU | bool | Boolean flag indicating whether additive delta ACU. |
| is_alertable | bool | Boolean flag indicating whether alertable. |
| is_allocation_imbalanced | bool | Boolean flag indicating whether allocation imbalanced. |
| is_app_isolation_enabled | bool | Boolean flag indicating whether app isolation enabled. |
| is_buffer_stablized | bool | Boolean flag indicating whether buffer stablized. |
| is_capacity_available | bool | Boolean flag indicating whether capacity available. |
| is_enabled | bool | Boolean flag indicating whether enabled. |
| is_falling_back_happened | bool | Boolean flag indicating whether falling back happened. |
| is_fetch_from_sf | bool | Boolean flag indicating whether fetch from sf. |
| is_file_present | bool | Boolean flag indicating whether file present. |
| is_full_node_process | bool | Boolean flag indicating whether full node process. |
| is_imbalance_reason_found | bool | Boolean flag indicating whether imbalance reason found. |
| is_imbalance_resolved | bool | Boolean flag indicating whether imbalance resolved. |
| is_initialized | bool | Boolean flag indicating whether initialized. |
| is_isolated | bool | Boolean flag indicating whether isolated. |
| is_logical_basis | bool | Boolean flag indicating whether logical basis. |
| is_max_vom_threshold_ignored | bool | Boolean flag indicating whether max vom threshold ignored. |
| is_new_max | bool | Boolean flag indicating whether new max. |
| is_node_overbooked | bool | Boolean flag indicating whether node overbooked. |
| is_out_of_disk | bool | Boolean flag indicating whether out of disk. |
| is_pool | bool | Boolean flag indicating whether pool. |
| is_process_in_job | bool | Boolean flag indicating whether process in job. |
| is_process_physical_memory_low | bool | Boolean flag indicating whether process physical memory low. |
| is_process_virtual_memory_low | bool | Boolean flag indicating whether process virtual memory low. |
| is_quota_hard | bool | Boolean flag indicating whether quota hard. |
| is_recursive | bool | Boolean flag indicating whether recursive. |
| is_remote_storage | long | Boolean flag indicating whether remote storage. |
| is_reported | bool | Boolean flag indicating whether reported. |
| is_slo_mismatch_ignored | bool | Boolean flag indicating whether slo mismatch ignored. |
| is_specified | bool | Boolean flag indicating whether specified. |
| is_split_across_pgs | bool | Boolean flag indicating whether split across pgs. |
| is_stable | bool | Boolean flag indicating whether stable. |
| is_static_affinity | bool | Boolean flag indicating whether static affinity. |
| is_success | bool | Boolean flag indicating whether success. |
| is_successful_write | bool | Boolean flag indicating whether successful write. |
| is_system_app_on_user_core | bool | Boolean flag indicating whether system app on user core. |
| is_system_physical_memory_high | bool | Boolean flag indicating whether system physical memory high. |
| is_system_physical_memory_low | bool | Boolean flag indicating whether system physical memory low. |
| is_trident_cache | bool | Boolean flag indicating whether trident cache. |
| is_trident_native | bool | Boolean flag indicating whether trident native. |
| is_utilization_based | bool | Boolean flag indicating whether utilization based. |
| is_violated | bool | Boolean flag indicating whether violated. |
| is_zombie | bool | Boolean flag indicating whether zombie. |
| is_zone_resilient | bool | Boolean flag indicating whether zone resilient. |
| isolated_cpus | long | Isolated cpus. |
| isolation_property_bag | string | Isolation property bag. |
| job_flags | long | Job flags. |
| job_name | string | Job name. |
| job_name_invalid | bool | Boolean flag indicating whether job name invalid. |
| job_obj_cap | long | Job obj cap. |
| job_object_cap | long | Job object cap. |
| job_object_limit_job_mem_kb | long | Job object limit job memory kb. |
| job_object_limit_process_mem_kb | long | Job object limit process memory kb. |
| json_telemetry_parse_result | string | Json telemetry parse result. |
| jumbo_packet | string | Jumbo packet. |
| kind | string | Kind. |
| last_access_time | long | Last access time timestamp. |
| last_modified_time | datetime | Last modified time timestamp. |
| last_stored_time | datetime | Last stored time timestamp. |
| last_write_time | long | Last write time timestamp. |
| lock_timeout_ms | long | Lock timeout ms in milliseconds. |
| manifest_name | string | Manifest name. |
| mapping_cpu_percent | long | Mapping CPU percentage. |
| mapping_number_of_cpus | long | Mapping number of cpus. |
| max_allowed_violated_cores | real | Maximum allowed violated cores. |
| max_app_count | long | Number of max app. |
| max_attempts | long | Maximum attempts. |
| max_commited_memory_mb | long | Maximum commited memory mb. |
| max_cpu_allocation_per_core | long | Maximum CPU allocation per core. |
| max_execution_time_ms | long | Maximum execution time ms. |
| max_expiry_time | datetime | Max expiry time timestamp. |
| max_idsu | long | Maximum idsu. |
| max_logical_cores | long | Maximum logical cores. |
| max_percent_cpu_rate | long | Maximum percentage CPU rate. |
| max_percent_dpc_time | real | Max percentage dpc time timestamp. |
| max_physical_memory_available_mb | long | Maximum physical memory available mb. |
| max_queue_time_ms | long | Maximum queue time ms. |
| max_threshold | long | Maximum threshold. |
| max_time_ms | long | Maximum time ms. |
| max_time_spent_waiting_ms | long | Maximum time spent waiting ms. |
| max_wait_time_ms | long | Maximum wait time ms. |
| max_write_throughput_mbps | long | Maximum write throughput mbps. |
| memory_cap | long | Memory cap. |
| memory_cap_job_object | long | Memory cap job object. |
| memory_clerk_name | string | Memory clerk name. |
| memory_clerk_type | string | Type classification for memory clerk. |
| memory_node_id | long | Memory node identifier. |
| memory_released_in_rm_phase_kb | long | Memory released in rm phase kb. |
| memory_usage_mb | long | Memory usage mb. |
| memory_utilization_pct | long | Memory utilization pct. |
| message | string | Human-readable message text. |
| message_count | long | Number of message. |
| message_type | long | Type classification for message. |
| metric | string | Metric. |
| metric_frq | long | Metric frq. |
| metric_name | string | Metric name. |
| metric_value | long | Metric value. |
| min_app_count | long | Number of min app. |
| min_execution_time_ms | long | Minimum execution time ms. |
| min_percent_dpc_time | real | Min percentage dpc time timestamp. |
| min_physical_memory_available_mb | long | Minimum physical memory available mb. |
| min_queue_time_ms | long | Minimum queue time ms. |
| min_threshold | long | Minimum threshold. |
| min_time_ms | long | Minimum time ms. |
| min_value_to_report_mb | long | Minimum value to report mb. |
| min_wait_time_ms | long | Minimum wait time ms. |
| move_cost | long | Move cost. |
| move_cost_run_status | long | Status value for move cost run. |
| multi_instance_mem_rg_action_name | string | Multi instance memory resource governor action name. |
| multi_instance_mem_rg_async_action_timeout_ms | long | Multi instance memory resource governor async action timeout ms in milliseconds. |
| multi_instance_mem_rg_category_instance_count | long | Number of multi instance memory resource governor category instance. |
| multi_instance_mem_rg_category_key_type | string | Type classification for multi instance memory resource governor category key. |
| multi_instance_mem_rg_category_key_value | long | Multi instance memory resource governor category key value. |
| multi_instance_mem_rg_category_memory_cap | real | Multi instance memory resource governor category memory cap. |
| multi_instance_mem_rg_category_memory_usage | real | Multi instance memory resource governor category memory usage. |
| multi_instance_mem_rg_category_violation_degree | real | Multi instance memory resource governor category violation degree. |
| multi_instance_mem_rg_current_state | string | State value for multi instance memory resource governor current. |
| multi_instance_mem_rg_hresult | long | Multi instance memory resource governor hresult. |
| multi_instance_mem_rg_instance_category | long | Multi instance memory resource governor instance category. |
| multi_instance_mem_rg_instance_name | string | Multi instance memory resource governor instance name. |
| multi_instance_mem_rg_interval_timeout_seconds | long | Multi instance memory resource governor interval timeout seconds. |
| multi_instance_mem_rg_is_enabled | bool | Boolean flag indicating whether multi instance memory resource governor enabled. |
| multi_instance_mem_rg_iteration_id | long | Multi instance memory resource governor iteration identifier. |
| multi_instance_mem_rg_max_physical_memory_available_mb | long | Multi instance memory resource governor max physical memory available mb. |
| multi_instance_mem_rg_max_vom_threshold | real | Multi instance memory resource governor max vom threshold. |
| multi_instance_mem_rg_maximum_reclaim_target_page_cost | real | Multi instance memory resource governor maximum reclaim target page cost. |
| multi_instance_mem_rg_min_physical_memory_available_mb | long | Multi instance memory resource governor min physical memory available mb. |
| multi_instance_mem_rg_multi_db_type | bool | Boolean flag indicating whether multi instance memory resource governor multi database type. |
| multi_instance_mem_rg_multi_db_type_protection_is_enabled | bool | Boolean flag indicating whether multi instance memory resource governor multi database type protection enabled. |
| multi_instance_mem_rg_notification | string | Multi instance memory resource governor notification. |
| multi_instance_mem_rg_policy_id | long | Multi instance memory resource governor policy identifier. |
| multi_instance_mem_rg_prev_state | string | State value for multi instance memory resource governor prev. |
| multi_instance_mem_rg_provisioned_mem_obr | long | Multi instance memory resource governor provisioned memory obr. |
| multi_instance_mem_rg_reclaim_policy_id | long | Multi instance memory resource governor reclaim policy identifier. |
| multi_instance_mem_rg_reclaim_target_pages | long | Multi instance memory resource governor reclaim target pages. |
| multi_instance_mem_rg_reclaim_timeout_seconds | long | Multi instance memory resource governor reclaim timeout seconds. |
| multi_instance_mem_rg_serverless_mem_obr | long | Multi instance memory resource governor serverless memory obr. |
| multi_instance_mem_rg_session_id | long | Multi instance memory resource governor session identifier. |
| multi_overbooking_fallback_iteration_threshold | long | Multi overbooking fallback iteration threshold. |
| multi_overbooking_iterations | long | Multi overbooking iterations. |
| multi_overbooking_mask | long | Multi overbooking mask. |
| mutex_name | string | Mutex name. |
| mutex_wait_time | long | Mutex wait time timestamp. |
| name | string | Object or resource name. |
| native_application_name | string | Native application name. |
| native_application_path | string | Native application path. |
| new_affinity | string | New affinity. |
| new_affinity_mask | string | New affinity mask. |
| new_application_affinity | string | New application affinity. |
| new_cap | long | New cap. |
| new_number_of_cpus | long | New number of cpus. |
| new_reclamation_pool | string | New reclamation pool. |
| new_tracking_cpu_percentage | long | New tracking CPU pe percentage. |
| new_value | long | New value. |
| next_dynamic_rg_state | long | State value for next dynamic resource governor. |
| node_capacity | long | Node capacity. |
| node_commit_memory_usage_mb | long | Node commit memory usage mb. |
| node_ephemeral_ports_used_capacity | long | Node ephemeral ports used capacity. |
| node_id | long | Node identifier. |
| node_last_memory_usage_mb | long | Node last memory usage mb. |
| node_last_user_cpu_usage | long | Node last user CPU usage. |
| node_mcu_capacity | long | Node mcu capacity. |
| node_memory_usage_mb | long | Node memory usage mb. |
| node_physical_memory_usage_mb | long | Node physical memory usage mb. |
| node_sku | string | Node sku. |
| node_used_capacity | real | Node used capacity. |
| node_user_cpu_usage | long | Node user CPU usage. |
| notification | string | Notification. |
| num_invalid_instances | long | Num invalid instances. |
| num_logical_cores | real | Num logical cores. |
| num_out_of_disk_errors | long | Num out of disk errors. |
| num_provisoning_instances | long | Num provisoning instances. |
| num_rss_queues | string | Num rss queues. |
| num_serverless_instances | long | Num serverless instances. |
| num_writes | long | Num writes. |
| number_logical_cores | long | Number logical cores. |
| number_of_actions | long | Number of actions. |
| number_of_cores_overcommitted | long | Number of cores overcommitted. |
| number_of_cpus | long | Number of cpus. |
| number_of_decrease_actions | long | Number of decrease actions. |
| number_of_increase_actions | long | Number of increase actions. |
| number_partitioned_app_lists | long | Number partitioned app lists. |
| ob_app_key | string | Ob app key. |
| old_affinity | string | Old affinity. |
| old_affinity_mask | string | Old affinity mask. |
| old_cap | long | Old cap. |
| old_isolated_cpus | string | Old isolated cpus. |
| old_max_cpu_allocation_per_core | long | Old max CPU allocation per core. |
| old_overbooking_ratio | long | Old overbooking ratio. |
| old_reclamation_pool | string | Old reclamation pool. |
| old_rg_mgr_overbooking_ratio_in_percentage | long | Old resource governor mgr overbooking ratio in pe percentage. |
| old_sellable_ratio | long | Old sellable ratio. |
| old_tr_differential_sellable_ratios | string | Old tr differential sellable ratios. |
| old_tr_overbooking_ratio | long | Old tr overbooking ratio. |
| old_tracking_cpu_percentage | long | Old tracking CPU pe percentage. |
| old_value | long | Old value. |
| operation | long | Operation. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| output_cpus | string | Output cpus. |
| overbooking_app_key | string | Overbooking app key. |
| overbooking_ratio | long | Overbooking ratio. |
| overbooking_type | string | Type classification for overbooking. |
| package | string | Package. |
| package_name | string | Package name. |
| pages_kb | long | Pages kb. |
| paging_files | string | Paging files. |
| partition_id | string | Partition identifier. |
| peak_job_memory_used_kb | long | Peak job memory used kb. |
| peak_process_memory_used_kb | long | Peak process memory used kb. |
| percent_cpu | long | Percent CPU. |
| percent_cpu_rate | long | Percent CPU rate. |
| physical_allocated_cpus | string | Physical allocated cpus. |
| pingpong_mask | long | Pingpong mask. |
| pipe_name | string | Pipe name. |
| policy | string | Policy. |
| pool_indicators | long | Pool indicators. |
| prev_dynamic_rg_state | long | State value for prev dynamic resource governor. |
| prev_multi_overbooking_iterations | long | Prev multi overbooking iterations. |
| prev_multi_overbooking_mask | long | Prev multi overbooking mask. |
| process_handle | string | Process handle. |
| process_id | long | Process identifier. |
| process_indicators | long | Process indicators. |
| process_name | string | Process name. |
| profile_period_ms | long | Profile period ms in milliseconds. |
| property_name | string | Property name. |
| provisioning_overbooking_ratio | real | Provisioning overbooking ratio. |
| provisoning_mem_cap | real | Provisoning memory cap. |
| provisoning_mem_usage | real | Provisoning memory usage. |
| query_time | datetime | Query time timestamp. |
| quota_limit | long | Quota limit. |
| rand_seed | long | Rand seed. |
| re_register | bool | Boolean flag indicating whether re register. |
| read_error_code | long | Read error code. |
| reason | string | Reason. |
| receive_buffers | string | Receive buffers. |
| reclaim_timeout_seconds | long | Reclaim timeout seconds. |
| reduce_privileges | long | Reduce privileges. |
| reduction_percent | long | Reduction percentage. |
| reduction_step | long | Reduction step. |
| reference_count | long | Number of reference. |
| reg_state | string | State value for reg. |
| registration_duration | long | Registration duration. |
| registration_status | long | Status value for registration. |
| registry_key | string | Registry key. |
| registry_path | string | Registry path. |
| registry_value | long | Registry value. |
| remaining_target_pages | real | Remaining target pages. |
| remove_when_expired | bool | Boolean flag indicating whether remove when expired. |
| replica_id | long | Replica identifier. |
| replica_type | long | Type classification for replica. |
| reporting_startup_time_ms | long | Reporting startup time ms in milliseconds. |
| requsted_cpus | long | Requsted cpus. |
| reserved_applications_remaining | long | Reserved applications remaining. |
| reserved_instances_remaining | long | Reserved instances remaining. |
| reserved_kb | long | Reserved kb. |
| reserved_value | real | Reserved value. |
| resource | string | Resource. |
| resource_name | string | Resource name. |
| resource_type | string | Type classification for resource. |
| result | long | Result. |
| result_desc | string | Result desc. |
| result_hresult | long | Result hresult. |
| return_count | long | Number of return. |
| revert_high_pm | string | Revert high pm. |
| rg_app_replica_type | long | Type classification for resource governor app replica. |
| rg_host_module | string | Resource governor host module. |
| rg_host_path | string | Resource governor host path. |
| rg_instance_process_id | long | Resource governor instance process identifier. |
| rg_manager_app | bool | Boolean flag indicating whether resource governor manager app. |
| rg_manager_svc | bool | Boolean flag indicating whether resource governor manager svc. |
| rg_mapping_version | long | Resource governor mapping version. |
| rg_mcu | long | Resource governor mcu. |
| rg_mgr_overbooking_ratio_in_percentage | long | Resource governor mgr overbooking ratio in pe percentage. |
| rg_slo | string | Resource governor slo. |
| ring_product_family | string | Ring product family. |
| rm_memory_pressure_phase | string | Rm memory pressure phase. |
| rss_base_proc_num | long | Rss base proc num. |
| rss_max_proc_num | long | Rss max proc num. |
| rss_max_processors | long | Rss max processors. |
| sample_count | long | Number of sample. |
| schedulers_number | long | Schedulers number. |
| section | string | Section. |
| sellable_ratio | long | Sellable ratio. |
| send_buffers | string | Send buffers. |
| sequence_number | long | Sequence number. |
| serverless_mem_cap | real | Serverless memory cap. |
| serverless_mem_usage | real | Serverless memory usage. |
| serverless_min_cpu | long | Serverless min CPU. |
| serverless_overbooking_ratio | real | Serverless overbooking ratio. |
| serverless_paused_state | string | State value for serverless paused. |
| service_manifest_name | string | Service manifest name. |
| service_name | string | Service name. |
| service_type_name | string | Service type name. |
| sessionName | string | Session Name. |
| session_id | string | Session identifier. |
| severityNumber | long | Severity Number. |
| severityText | string | Severity Text. |
| shared_committed_kb | long | Shared committed kb. |
| shared_ma_usage | long | Shared ma usage. |
| should_report_delta_acu | bool | Boolean flag indicating whether should report delta acu. |
| should_report_delta_amu | bool | Boolean flag indicating whether should report delta amu. |
| size | long | Size. |
| size_after_mb | long | Size after mb. |
| size_before_mb | long | Size before mb. |
| sleep_duration | long | Sleep duration. |
| slo_cap | long | Slo cap. |
| slo_size | string | Slo size. |
| smb_multichannel_connection_json | string | Smb multichannel connection json. |
| smcu_value | long | Smcu value. |
| soft_cpu_rate | bool | Boolean flag indicating whether soft CPU rate. |
| sos_result | long | Sos result. |
| source | long | Source. |
| source_id | string | Source identifier. |
| space_to_reserve | long | Space to reserve. |
| space_to_reserve_reported | long | Space to reserve reported. |
| spinnaker_usage | long | Spinnaker usage. |
| state | long | Current lifecycle or health state. |
| state_after | string | State after. |
| state_before | string | State before. |
| status_message | string | Status message. |
| success | bool | Boolean flag indicating whether success. |
| system_app_on_user_core | string | System app on user core. |
| system_app_on_user_core_usage | long | System app on user core usage. |
| system_group_affinity | string | System group affinity. |
| system_indicators | long | System indicators. |
| system_thread_id | long | System thread identifier. |
| target_directory | string | Target directory. |
| target_kb | long | Target kb. |
| target_pages_reclaimed_from_old_reclamation_pool | real | Target pages reclaimed from old reclamation pool. |
| target_size_mb | long | Target size mb. |
| target_slo | string | Target slo. |
| target_slo_cap | real | Target slo cap. |
| target_throughput_mbps | long | Target throughput mbps. |
| target_write_throughput_mbps | long | Target write throughput mbps. |
| task_trigger | long | Task trigger. |
| thread_name | string | Thread name. |
| throttled_instances | string | Throttled instances. |
| time_to_live_in_seconds | long | Time to live in seconds. |
| timeout_ms | long | Timeout ms in milliseconds. |
| timer_name | string | Timer name. |
| timer_period | long | Timer period. |
| timestamp_resource_monitor_ring_buffer_recorded | long | Timestamp resource monitor ring buffer recorded. |
| topology | string | Topology. |
| total_app_ephemeral_ports_used | long | Total app ephemeral ports used. |
| total_app_mcu_usage | long | Total app mcu usage. |
| total_calculated_time_to_wait_ms | long | Total calculated time to wait ms. |
| total_elapsed_time_ms | long | Total elapsed time ms. |
| total_ephemeral_ports_used | long | Total ephemeral ports used. |
| total_isolated_mcu_used | long | Total isolated mcu used. |
| total_memory_free_block_emergency_descriptors | long | Total memory free block emergency descriptors. |
| total_non_isolated_mcu_used | long | Total non isolated mcu used. |
| total_page_file_kb | long | Total page file kb. |
| total_physical_memory_kb | long | Total physical memory kb. |
| total_time_spent_waiting_ms | long | Total time spent waiting ms. |
| total_virtual_address_space_kb | long | Total virtual address space kb. |
| tr_differential_sellable_ratios | string | Tr differential sellable ratios. |
| tr_overbooking_ratio | long | Tr overbooking ratio. |
| trace_keyword | string | Trace keyword. |
| trace_level | long | Trace level. |
| transient_error | bool | Boolean flag indicating whether transient error. |
| trigger_threshold_mb | long | Trigger threshold mb. |
| usage_affinity_per_app | string | Usage affinity per app. |
| use_real_disk_capacity | bool | Boolean flag indicating whether use real disk capacity. |
| user_data | bool | Boolean flag indicating whether user data. |
| value | long | Value. |
| version | long | Version. |
| version_build | long | Version build. |
| version_major | long | Version major. |
| version_minor | long | Version minor. |
| version_revision | long | Version revision. |
| violated_apps | string | Violated apps. |
| violation_duration | long | Violation duration. |
| violation_duration_threshold | long | Violation duration threshold. |
| violation_number | long | Violation number. |
| violation_threshold | real | Violation threshold. |
| violation_type | string | Type classification for violation. |
| vm_committed_kb | long | Vm committed kb. |
| vm_size | string | Vm size. |
| wall_clock_time_ms | long | Wall clock time ms in milliseconds. |
| was_force_stopped | bool | Boolean flag indicating whether was force stopped. |
| wf_local_mcu | long | Wf local mcu. |
| wf_remote_mcu | long | Wf remote mcu. |
| win32_error_code | long | Win32 error code. |
| winfab_slo | string | Winfab slo. |
| worker_pool_cap | long | Worker pool cap. |
| working_directory_path | string | Working directory path. |
| write_error_code | long | Write error code. |
| xagent_registry_path | string | Xagent registry path. |
| xagent_registry_value | string | Xagent registry value. |
| xml_path | string | Xml path. |
| xperf_flavor | long | Xperf flavor. |
| xperf_mode | long | Xperf mode. |
| xsd_path | string | Xsd path. |

## MonSqlCaches — SQL Caches

**Purpose**: SQL Caches. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| buckets_avg_length | long | Buckets avg length. |
| buckets_avg_scan_hit_length | long | Buckets avg scan hit length. |
| buckets_avg_scan_miss_length | long | Buckets avg scan miss length. |
| buckets_count | long | Number of buckets. |
| buckets_in_use_count | long | Number of buckets in use. |
| buckets_max_length | long | Buckets max length. |
| buckets_max_length_ever | long | Buckets max length ever. |
| buckets_min_length | long | Buckets min length. |
| cache_inuse_kb | long | Cache inuse kb. |
| cache_pages_kb | long | Cache pages kb. |
| cache_pmo_kb | long | Cache pmo kb. |
| clock_hand_id | long | Clock hand identifier. |
| code_package_version | string | Code package version. |
| different_pool_all_rounds | long | Different pool all rounds. |
| entries_avg_cost | long | Entries avg cost. |
| entries_avg_size_kb | long | Entries avg size kb. |
| entries_max_cost | long | Entries max cost. |
| entries_max_size_kb | long | Entries max size kb. |
| entries_min_cost | long | Entries min cost. |
| entries_min_size_kb | long | Entries min size kb. |
| entries_popped | long | Entries popped. |
| entries_pushed | long | Entries pushed. |
| entries_soft_quota | long | Entries soft quota. |
| entries_total_size_kb | long | Entries total size kb. |
| event | string | Event name emitted by the component. |
| global_internal_pressure_enabled | bool | Boolean flag indicating whether global internal pressure enabled. |
| hash_tbl_hit_length | long | Hash tbl hit length. |
| hash_tbl_hits | long | Hash tbl hits. |
| hash_tbl_misses | long | Hash tbl misses. |
| hash_tbl_misses_length | long | Hash tbl misses length. |
| hits_count | long | Number of hits. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| in_use_all_rounds | long | In use all rounds. |
| invisible_all_rounds | long | Invisible all rounds. |
| is_process_physical_memory_low | bool | Boolean flag indicating whether process physical memory low. |
| is_process_virtual_memory_low | bool | Boolean flag indicating whether process virtual memory low. |
| is_system_physical_memory_low | bool | Boolean flag indicating whether system physical memory low. |
| last_round_start | long | Last round start. |
| last_tick_time | long | Last tick time timestamp. |
| logical_database_guid | string | Logical database guid. |
| logical_database_name | string | Logical database name. |
| marked_should_not_remove_all_rounds | long | Marked should not remove all rounds. |
| max_entries_per_tick_in_curr_round | long | Maximum entries per tick in curr round. |
| min_entries_per_tick_in_curr_round | long | Minimum entries per tick in curr round. |
| misses_count | long | Number of misses. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| physical_database_guid | string | Physical database guid. |
| pinned_all_rounds | long | Pinned all rounds. |
| pool_physical_memory_indicator_mask | long | Pool physical memory indicator mask. |
| removed_all_rounds | long | Removed all rounds. |
| removed_curr_round | long | Removed curr round. |
| removed_last_round | long | Removed last round. |
| rounds_count | long | Number of rounds. |
| sessionName | string | Session Name. |
| size_freed_curr_round_kb | long | Size freed curr round kb. |
| size_freed_last_round_kb | long | Size freed last round kb. |
| store_address | string | Store address. |
| store_entries | long | Store entries. |
| store_hard_quota | long | Store hard quota. |
| store_hits | long | Store hits. |
| store_misses | long | Store misses. |
| store_name | string | Store name. |
| store_soft_quota | long | Store soft quota. |
| store_type | string | Type classification for store. |
| store_type_soft_quota | long | Store type soft quota. |
| store_type_soft_quota_reached | bool | Boolean flag indicating whether store type soft quota reached. |
| table_level | long | Table level. |
| tag_id | long | Tag identifier. |
| time_elapsed_ms | long | Time elapsed ms in milliseconds. |
| time_of_last_round | long | Time of last round. |
| time_waiting_for_node_clock_ms | long | Time waiting for node clock ms in milliseconds. |
| time_waiting_for_process_clock_ms | long | Time waiting for process clock ms in milliseconds. |
| updated_last_round | long | Updated last round. |
| visited_all_rounds | long | Visited all rounds. |
| visited_curr_round | long | Visited curr round. |
| visited_last_round | long | Visited last round. |

## MonSqlMemNodeOomRingBuffer — SQL Memory Node OOM Ring Buffer

**Purpose**: SQL Memory Node OOM Ring Buffer. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| attach_activity_id | string | Attach activity identifier. |
| attach_activity_id_xfer | string | Attach activity id xfer. |
| attempts | long | Attempts. |
| available_extended_virtual_address_space_kb | long | Available extended virtual address space kb. |
| available_memory_free_block_emergency_descriptors | long | Available memory free block emergency descriptors. |
| available_page_file_kb | long | Available page file kb. |
| available_physical_memory_kb | long | Available physical memory kb. |
| available_virtual_address_space_kb | long | Available virtual address space kb. |
| awe_kb | long | Awe kb. |
| call_stack | string | Call stack. |
| callstack | string | Callstack. |
| callstack_rva | string | Callstack rva. |
| code_package_version | string | Code package version. |
| committed_kb | long | Committed kb. |
| event | string | Event name emitted by the component. |
| factor | string | Factor. |
| failure | string | Failure. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| id | long | identifier. |
| instance_rg_size | string | Instance resource governor size. |
| is_process_in_job | bool | Boolean flag indicating whether process in job. |
| is_process_physical_memory_low | bool | Boolean flag indicating whether process physical memory low. |
| is_process_virtual_memory_low | bool | Boolean flag indicating whether process virtual memory low. |
| is_system_physical_memory_high | bool | Boolean flag indicating whether system physical memory high. |
| is_system_physical_memory_low | bool | Boolean flag indicating whether system physical memory low. |
| job_object_limit_job_mem_kb | long | Job object limit job memory kb. |
| job_object_limit_process_mem_kb | long | Job object limit process memory kb. |
| last_error | long | Last error. |
| low_memory_guard_wait_time_ms | long | Low memory guard wait time ms in milliseconds. |
| memory_free_block_emergency_allocator_attempted | bool | Boolean flag indicating whether memory free block emergency allocator attempted. |
| memory_node_id | long | Memory node identifier. |
| memory_utilization_pct | long | Memory utilization pct. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| pages_kb | long | Pages kb. |
| peak_job_memory_used_kb | long | Peak job memory used kb. |
| peak_process_memory_used_kb | long | Peak process memory used kb. |
| pool_metadata_id | long | Pool metadata identifier. |
| process_id | long | Process identifier. |
| reserved_kb | long | Reserved kb. |
| resources | long | Resources. |
| sessionName | string | Session Name. |
| session_id | long | Session identifier. |
| severity_level | long | Severity level. |
| shared_committed_kb | long | Shared committed kb. |
| system_thread_id | long | System thread identifier. |
| target_kb | long | Target kb. |
| task | string | Task. |
| time_spent | long | Time spent. |
| timestamp_memory_node_oom_ring_buffer_recorded | long | Timestamp memory node OOM ring buffer recorded. |
| total_memory_free_block_emergency_descriptors | long | Total memory free block emergency descriptors. |
| total_page_file_kb | long | Total page file kb. |
| total_physical_memory_kb | long | Total physical memory kb. |
| total_virtual_address_space_kb | long | Total virtual address space kb. |
| tsql_stack | string | Tsql stack. |

## MonSqlMemoryClerkStats — SQL Memory Clerk Stats

**Purpose**: SQL Memory Clerk Stats. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: availability, performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| allocated_kb | long | Allocated kb. |
| attach_activity_id | string | Attach activity identifier. |
| attach_activity_id_xfer | string | Attach activity id xfer. |
| avg_allocation_time_usec | real | Average allocation time usec. |
| avg_recent_allocation_time_usec | real | Average recent allocation time usec. |
| broker_clerk_name | string | Broker clerk name. |
| code_package_version | string | Code package version. |
| comment | string | Comment. |
| current_utilzation_percent | real | Current utilzation percentage. |
| delta_allocated_multi_pages_kb | long | Delta allocated multi pages kb. |
| delta_memory_allocated_kb | long | Delta memory allocated kb. |
| delta_number_of_greater_than_16mb_allocations | long | Delta number of greater than 16mb allocations. |
| delta_number_of_greater_than_2mb_allocations | long | Delta number of greater than 2mb allocations. |
| delta_number_of_greater_than_4mb_allocations | long | Delta number of greater than 4mb allocations. |
| delta_number_of_greater_than_8mb_allocations | long | Delta number of greater than 8mb allocations. |
| delta_number_of_greater_than_top_level_blk_size_allocations | long | Delta number of greater than top level blk size allocations. |
| duration_ms | long | Duration in milliseconds. |
| event | string | Event name emitted by the component. |
| external_benefit | real | External benefit. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| internal_benefit | real | Internal benefit. |
| internal_freed_pages | long | Internal freed pages. |
| max_allocation_time_usec | real | Maximum allocation time usec. |
| max_memory_released_by_rm_kb | long | Maximum memory released by rm kb. |
| max_recent_allocation_time_usec | real | Maximum recent allocation time usec. |
| memobj_type_name | string | Memobj type name. |
| memory_clerk_name | string | Memory clerk name. |
| memory_clerk_type | string | Type classification for memory clerk. |
| memory_node_id | long | Memory node identifier. |
| node_id | long | Node identifier. |
| notify_time_max_ms | long | Notify time max ms in milliseconds. |
| notify_time_ms | long | Notify time ms in milliseconds. |
| notify_time_samples_count | long | Number of notify time samples. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| pages_kb | long | Pages kb. |
| peak_pages_kb | long | Peak pages kb. |
| periodic_freed_pages | long | Periodic freed pages. |
| process_id | long | Process identifier. |
| recent_allocations | long | Recent allocations. |
| sessionName | string | Session Name. |
| simulated_pages | long | Simulated pages. |
| simulation_benefit | real | Simulation benefit. |
| stats_name | string | Stats name. |
| system_thread_id | long | System thread identifier. |
| timer_frequency_ms | long | Timer frequency ms in milliseconds. |
| total_allocations | long | Total allocations. |
| total_folders_created | long | Total folders created. |
| total_folders_deleted | long | Total folders deleted. |
| total_folding_pmo_count | long | Number of total folding pmo. |
| total_memory_released_by_rm_kb | long | Total memory released by rm kb. |
| total_pages | long | Total pages. |
| total_pmo_count | long | Number of total pmo. |
| type_pages_kb | long | Type pages kb. |
| value_of_memory | real | Value of memory. |
| vm_committed_kb | long | Vm committed kb. |
| wasted_pages_kb | long | Wasted pages kb. |

## MonSqlRgHistory — SQL resource governor History

**Purpose**: SQL resource governor History. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: availability, backup-restore, performance. Often used to explain wait or latency patterns. Often used during backup or restore investigations.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| active_memgrant_count | long | Number of active memgrant. |
| active_memgrant_count_avg | float | Active memgrant count avg. |
| active_memgrant_count_max | long | Active memgrant count max. |
| active_memgrant_kb | long | Active memgrant kb. |
| active_memgrant_kb_avg | float | Active memgrant kb avg. |
| active_memgrant_kb_max | long | Active memgrant kb max. |
| active_outbound_connection_worker_count_avg | real | Active outbound connection worker count avg. |
| active_outbound_connection_worker_count_max | long | Active outbound connection worker count max. |
| active_request_count | long | Number of active request. |
| active_request_count_avg | float | Active request count avg. |
| active_request_count_max | long | Active request count max. |
| active_session_count_avg | float | Active session count avg. |
| active_session_count_max | long | Active session count max. |
| active_worker_avg | long | Active worker avg. |
| active_worker_count | long | Number of active worker. |
| active_worker_max | long | Active worker max. |
| active_worker_min | long | Active worker min. |
| active_workers_count | long | Number of active workers. |
| agg_active_workers_count | long | Number of agg active workers. |
| agg_current_workers_count | long | Number of agg current workers. |
| agg_idle_switches_count | long | Number of agg idle switches. |
| agg_pending_disk_io_count | long | Number of agg pending disk I/O. |
| agg_queued_disk_io_count | long | Number of agg queued disk I/O. |
| agg_spinlock_wait_count | long | Number of agg spinlock wait. |
| agg_spinlock_wait_time_ms | long | Agg spinlock wait time ms in milliseconds. |
| agg_total_signal_time_ms | long | Agg total signal time ms in milliseconds. |
| agg_total_waits_completed | long | Agg total waits completed. |
| agg_yield_count | long | Number of agg yield. |
| alternate_io_factor | long | Alternate I/O factor. |
| attach_activity_id | string | Attach activity identifier. |
| attach_activity_id_xfer | string | Attach activity id xfer. |
| avg_cpu_percent | real | Average CPU utilization percentage. |
| avg_cpu_percent_scaled | real | Average CPU percentage scaled. |
| background_write_bytes_total_per_second_max | float | Background write size in bytes total per second max. |
| background_write_bytes_total_per_second_min | float | Background write size in bytes total per second min. |
| background_writes_total_per_second_max | float | Background writes total per second max. |
| background_writes_total_per_second_min | float | Background writes total per second min. |
| billable_read_ios_completed_per_second_max | float | Billable read ios completed per second max. |
| billable_read_ios_completed_per_second_min | float | Billable read ios completed per second min. |
| billable_read_ios_issued_per_second_max | float | Billable read ios issued per second max. |
| billable_read_ios_issued_per_second_min | float | Billable read ios issued per second min. |
| billable_write_ios_completed_per_second_max | float | Billable write ios completed per second max. |
| billable_write_ios_completed_per_second_min | float | Billable write ios completed per second min. |
| billable_write_ios_issued_per_second_max | float | Billable write ios issued per second max. |
| billable_write_ios_issued_per_second_min | float | Billable write ios issued per second min. |
| blocked_task_count_avg | real | Blocked task count avg. |
| blocked_task_count_max | long | Blocked task count max. |
| bytes_total_per_second_max | real | Bytes total per second max. |
| cache_memory_kb | long | Cache memory kb. |
| cache_memory_kb_avg | float | Cache memory kb avg. |
| cache_memory_kb_max | long | Cache memory kb max. |
| cap_cpu | real | Cap CPU. |
| code_package_start_time | long | Code package start time timestamp. |
| code_package_version | string | Code package version. |
| codepath_used | long | Codepath used. |
| compile_memory_kb | long | Compile memory kb. |
| compile_memory_kb_avg | float | Compile memory kb avg. |
| compile_memory_kb_max | long | Compile memory kb max. |
| concurrent_request_cap | long | Concurrent request cap. |
| count_receives | long | Number of count receives. |
| count_receives_throttled | long | Number of count receives throttled. |
| count_sends | long | Number of count sends. |
| count_sends_throttled | long | Number of count sends throttled. |
| cpu_cap_sec | real | CPU cap sec. |
| cpu_id | long | CPU identifier. |
| credit_expiry_date | datetime | Credit expiry date. |
| current_tasks_count | long | Number of current tasks. |
| current_workers_count | long | Number of current workers. |
| dac_schedulers_count | long | Number of dac schedulers. |
| data_space_cap_kb | long | Data space cap kb. |
| database_id | long | Database identifier. |
| db_name | string | Database name. |
| delta_background_write_bytes_total | long | Delta background write size in bytes total. |
| delta_background_writes_total | long | Delta background writes total. |
| delta_billable_read_ios_completed | long | Delta billable read ios completed. |
| delta_billable_read_ios_issued | long | Delta billable read ios issued. |
| delta_billable_write_ios_completed | long | Delta billable write ios completed. |
| delta_billable_write_ios_issued | long | Delta billable write ios issued. |
| delta_context_switch_io_completion_time_ms | long | Delta context switch I/O completion time ms in milliseconds. |
| delta_context_switch_io_issue_time_ms | long | Delta context switch I/O issue time ms in milliseconds. |
| delta_context_switch_time_ms | long | Delta context switch time ms in milliseconds. |
| delta_context_switches_count | long | Number of delta context switches. |
| delta_dirty_page_count | long | Number of delta dirty page. |
| delta_idle_consumed_time_ms | long | Delta idle consumed time ms in milliseconds. |
| delta_idle_switches_count | long | Number of delta idle switches. |
| delta_idle_time_ms | long | Delta idle time ms in milliseconds. |
| delta_io_active_time_ms | long | Delta I/O active time ms in milliseconds. |
| delta_io_issue_delay_non_throttled_total_ms | long | Delta I/O issue delay non throttled total ms in milliseconds. |
| delta_io_issue_delay_total_ms | long | Delta I/O issue delay total ms in milliseconds. |
| delta_io_queue_limit_wait_count_total | long | Delta I/O queue limit wait count total. |
| delta_io_stall | long | Delta I/O stall. |
| delta_io_stall_queued_read_ms | long | Delta I/O stall queued read ms in milliseconds. |
| delta_io_stall_queued_write_ms | long | Delta I/O stall queued write ms in milliseconds. |
| delta_io_stall_read_ms | long | Delta I/O stall read ms in milliseconds. |
| delta_io_stall_write_ms | long | Delta I/O stall write ms in milliseconds. |
| delta_ios_group_iops_delayed | long | Delta ios group IOPS delayed. |
| delta_ios_local_volume_iops_delayed | long | Delta ios local volume IOPS delayed. |
| delta_ios_local_volume_throughput_delayed | long | Delta ios local volume throughput delayed. |
| delta_ios_not_delayed | long | Delta ios not delayed. |
| delta_ios_pool_iops_delayed | long | Delta ios pool IOPS delayed. |
| delta_ios_volume_iops_delayed | long | Delta ios volume IOPS delayed. |
| delta_ios_volume_throughput_delayed | long | Delta ios volume throughput delayed. |
| delta_ios_volume_type_iops_delayed | long | Delta ios volume type IOPS delayed. |
| delta_ios_volume_type_throughput_delayed | long | Delta ios volume type throughput delayed. |
| delta_issue_failures_due_to_insufficient_stack | long | Delta issue failures due to insufficient stack. |
| delta_issue_failures_due_to_storage_subsystem | long | Delta issue failures due to storage subsystem. |
| delta_issue_failures_due_to_volume_limit | long | Delta issue failures due to volume limit. |
| delta_lazy_preemptive_switches_count | long | Number of delta lazy preemptive switches. |
| delta_lock_wait_count | long | Number of delta lock wait. |
| delta_lock_wait_time_ms | long | Delta lock wait time ms in milliseconds. |
| delta_log_bytes_used_total | long | Delta log size in bytes used total. |
| delta_log_commits_tracked_total | long | Delta log commits tracked total. |
| delta_log_non_xact_bytes_total | long | Delta log non xact size in bytes total. |
| delta_log_non_xact_governed_bytes_total | long | Delta log non xact governed size in bytes total. |
| delta_log_operations_tracked_total | long | Delta log operations tracked total. |
| delta_log_overhead_bytes_total | long | Delta log overhead size in bytes total. |
| delta_log_temp_db_bytes_used_total | long | Delta log temp database size in bytes used total. |
| delta_log_time_waited_for_allotment_total_ms | long | Delta log time waited for allotment total ms in milliseconds. |
| delta_log_waits_for_allotment_total | long | Delta log waits for allotment total. |
| delta_memgrant_waiter_count | long | Number of delta memgrant waiter. |
| delta_normalized_ios_completed_total | long | Delta normalized ios completed total. |
| delta_normalized_read_ios_completed | long | Delta normalized read ios completed. |
| delta_normalized_read_ios_issued | long | Delta normalized read ios issued. |
| delta_normalized_reads_completed_total | long | Delta normalized reads completed total. |
| delta_normalized_reads_issued_total | long | Delta normalized reads issued total. |
| delta_normalized_reads_throttled_total | long | Delta normalized reads throttled total. |
| delta_normalized_write_ios_completed | long | Delta normalized write ios completed. |
| delta_normalized_write_ios_issued | long | Delta normalized write ios issued. |
| delta_normalized_writes_completed_total | long | Delta normalized writes completed total. |
| delta_normalized_writes_issued_total | long | Delta normalized writes issued total. |
| delta_normalized_writes_throttled_total | long | Delta normalized writes throttled total. |
| delta_num_of_bytes_read | long | Delta num of size in bytes read. |
| delta_num_of_bytes_written | long | Delta num of size in bytes written. |
| delta_num_of_reads | long | Delta num of reads. |
| delta_num_of_writes | long | Delta num of writes. |
| delta_out_of_memory_count | long | Number of delta out of memory. |
| delta_preemptive_switches_count | long | Number of delta preemptive switches. |
| delta_read_ahead_count | long | Number of delta read ahead. |
| delta_read_ahead_pages_count | long | Number of delta read ahead pages. |
| delta_read_bytes_total | long | Delta read size in bytes total. |
| delta_read_io_completed_total | long | Delta read I/O completed total. |
| delta_read_io_issued_total | long | Delta read I/O issued total. |
| delta_read_io_queued_total | long | Delta read I/O queued total. |
| delta_read_io_stall_queued_ms | long | Delta read I/O stall queued ms in milliseconds. |
| delta_read_io_stall_total_ms | long | Delta read I/O stall total ms in milliseconds. |
| delta_read_io_throttled_total | long | Delta read I/O throttled total. |
| delta_read_stall_queued_ms | long | Delta read stall queued ms in milliseconds. |
| delta_read_stall_total_ms | long | Delta read stall total ms in milliseconds. |
| delta_reads_completed_total | long | Delta reads completed total. |
| delta_reads_issued_total | long | Delta reads issued total. |
| delta_reads_queued_total | long | Delta reads queued total. |
| delta_reads_throttled_total | long | Delta reads throttled total. |
| delta_reserved_io_limited_by_volume_total | long | Delta reserved I/O limited by volume total. |
| delta_reserved_reads_failed | long | Delta reserved reads failed. |
| delta_reserved_reads_hit_vol_limit | long | Delta reserved reads hit vol limit. |
| delta_reserved_writes_failed | long | Delta reserved writes failed. |
| delta_reserved_writes_hit_vol_limit | long | Delta reserved writes hit vol limit. |
| delta_shared_reads_failed | long | Delta shared reads failed. |
| delta_shared_reads_hit_vol_limit | long | Delta shared reads hit vol limit. |
| delta_shared_writes_failed | long | Delta shared writes failed. |
| delta_shared_writes_hit_vol_limit | long | Delta shared writes hit vol limit. |
| delta_size_on_disk_bytes | long | Delta size on disk size in bytes. |
| delta_spinlock_wait_count | long | Number of delta spinlock wait. |
| delta_spinlock_wait_time_ms | long | Delta spinlock wait time ms in milliseconds. |
| delta_total_completed_tasks | long | Delta total completed tasks. |
| delta_total_cpu_active_ms | long | Delta total CPU active ms in milliseconds. |
| delta_total_cpu_delayed_ms | long | Delta total CPU delayed ms in milliseconds. |
| delta_total_cpu_idle_capped_ms | long | Delta total CPU idle capped ms in milliseconds. |
| delta_total_cpu_usage_actual_ms | long | Delta total CPU usage actual ms in milliseconds. |
| delta_total_cpu_usage_ms | long | Delta total CPU usage ms in milliseconds. |
| delta_total_cpu_usage_preemptive_ms | long | Delta total CPU usage preemptive ms in milliseconds. |
| delta_total_cpu_violation_delay_ms | long | Delta total CPU violation delay ms in milliseconds. |
| delta_total_enqueued_tasks | long | Delta total enqueued tasks. |
| delta_total_io_queue_limit_ms | long | Delta total I/O queue limit ms in milliseconds. |
| delta_total_memgrant_count | long | Number of delta total memgrant. |
| delta_total_memgrant_timeout_count | long | Number of delta total memgrant timeout. |
| delta_total_no_load_balance | long | Delta total no load balance. |
| delta_total_query_optimization_count | long | Number of delta total query optimization. |
| delta_total_reduced_memgrant_count | long | Number of delta total reduced memgrant. |
| delta_total_request_count | long | Number of delta total request. |
| delta_total_scheduler_delay_ms | long | Delta total scheduler delay ms in milliseconds. |
| delta_total_signal_wait_time_ms | long | Delta total signal wait time ms in milliseconds. |
| delta_total_spinlock_sleep_ms | long | Delta total spinlock sleep ms in milliseconds. |
| delta_total_suboptimal_plan_generation_count | long | Number of delta total suboptimal plan generation. |
| delta_waits_completed | long | Delta waits completed. |
| delta_write_bytes_total | long | Delta write size in bytes total. |
| delta_write_io_completed_total | long | Delta write I/O completed total. |
| delta_write_io_issued_total | long | Delta write I/O issued total. |
| delta_write_io_queued_total | long | Delta write I/O queued total. |
| delta_write_io_stall_queued_ms | long | Delta write I/O stall queued ms in milliseconds. |
| delta_write_io_stall_total_ms | long | Delta write I/O stall total ms in milliseconds. |
| delta_write_io_throttled_total | long | Delta write I/O throttled total. |
| delta_write_stall_queued_ms | long | Delta write stall queued ms in milliseconds. |
| delta_write_stall_total_ms | long | Delta write stall total ms in milliseconds. |
| delta_writes_completed_total | long | Delta writes completed total. |
| delta_writes_issued_total | long | Delta writes issued total. |
| delta_writes_queued_total | long | Delta writes queued total. |
| delta_writes_throttled_total | long | Delta writes throttled total. |
| delta_yield_count | long | Number of delta yield. |
| dirty_page_count | long | Number of dirty page. |
| dirty_page_count_per_second_max | float | Dirty page count per second max. |
| dirty_page_count_per_second_min | float | Dirty page count per second min. |
| duration_ms | long | Duration in milliseconds. |
| duration_time_ms | long | Duration time ms in milliseconds. |
| elapsed_time_ms | long | Elapsed time ms in milliseconds. |
| end_aggregated_sample | datetime | End aggregated sample. |
| end_of_last_granular_sample | datetime | End of last granular sample. |
| error_code | long | Numeric error code for the failure or event. |
| event | string | Event name emitted by the component. |
| fcb_type | int | Type classification for fcb. |
| file_count | long | Number of file. |
| file_handle | long | File handle. |
| file_id | long | File identifier. |
| file_name | string | File name. |
| file_path | string | File path. |
| file_share_path | string | File share path. |
| free_credits_remaining | long | Free credits remaining. |
| free_limit_value | long | Free limit value. |
| global_io_cap | long | Global I/O cap. |
| governor_token_bucket_depth_bw | long | Governor token bucket depth bw. |
| governor_token_bucket_depth_io | long | Governor token bucket depth I/O. |
| governor_token_bucket_fill_interval_ms | long | Governor token bucket fill interval ms in milliseconds. |
| governor_token_bucket_fill_rate_per_second_bw | long | Governor token bucket fill rate per second bw. |
| governor_token_bucket_fill_rate_per_second_io | long | Governor token bucket fill rate per second I/O. |
| group_id | long | Group identifier. |
| group_name | string | Group name. |
| growth | long | Growth. |
| head_group_id | long | Head group identifier. |
| head_group_name | string | Head group name. |
| hidden_schedulers_count | long | Number of hidden schedulers. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| ideal_workers_limit | long | Ideal workers limit. |
| idle_workers_count | long | Number of idle workers. |
| instance_rg_size | string | Instance resource governor size. |
| io_active_time_ms_per_second_max | float | I/O active time ms per second max. |
| io_active_time_ms_per_second_min | float | I/O active time ms per second min. |
| io_cap | long | I/O cap. |
| io_issue_delay_total_ms_per_second_max | float | I/O issue delay total ms per second max. |
| io_issue_delay_total_ms_per_second_min | float | I/O issue delay total ms per second min. |
| io_size_category | long | I/O size category. |
| io_stall_per_second_max | float | I/O stall per second max. |
| io_stall_per_second_min | float | I/O stall per second min. |
| io_stall_queued_read_ms_per_second_max | float | I/O stall queued read ms per second max. |
| io_stall_queued_read_ms_per_second_min | float | I/O stall queued read ms per second min. |
| io_stall_queued_write_ms_per_second_max | float | I/O stall queued write ms per second max. |
| io_stall_queued_write_ms_per_second_min | float | I/O stall queued write ms per second min. |
| io_stall_read_ms_per_second_max | float | I/O stall read ms per second max. |
| io_stall_read_ms_per_second_min | float | I/O stall read ms per second min. |
| io_stall_write_ms_per_second_max | float | I/O stall write ms per second max. |
| io_stall_write_ms_per_second_min | float | I/O stall write ms per second min. |
| iops_per_volume_cap | real | IOPS per volume cap. |
| ios_completed_total_per_second_max | real | Ios completed total per second max. |
| ios_issued_total_per_second_max | real | Ios issued total per second max. |
| ios_queued_total_per_second_max | real | Ios queued total per second max. |
| ios_stall_queued_ms_per_second_max | real | Ios stall queued ms per second max. |
| ios_stall_total_ms_per_second_max | real | Ios stall total ms per second max. |
| is_agg_volume | bool | Boolean flag indicating whether agg volume. |
| is_categorized | bool | Boolean flag indicating whether categorized. |
| is_eligible_for_force_pause | bool | Boolean flag indicating whether eligible for force pause. |
| is_for_log | bool | Boolean flag indicating whether for log. |
| is_for_write | bool | Boolean flag indicating whether for write. |
| is_idle | bool | Boolean flag indicating whether idle. |
| is_primary_replica | bool | Boolean flag indicating whether primary replica. |
| latency_bucket_high | long | Latency bucket high. |
| latency_bucket_low | long | Latency bucket low. |
| latency_bucket_medium | long | Latency bucket medium. |
| latency_bucket_moderate_high | long | Latency bucket moderate high. |
| latency_bucket_very_low | long | Latency bucket very low. |
| latency_max_us_very_high | long | Latency max us very high. |
| latency_square_sum_ms | long | Latency square sum ms in milliseconds. |
| latency_square_sum_ms_high | long | Latency square sum ms high. |
| latency_square_sum_ms_low | long | Latency square sum ms low. |
| latency_square_sum_ms_medium | long | Latency square sum ms medium. |
| latency_square_sum_ms_moderate_high | long | Latency square sum ms moderate high. |
| latency_square_sum_ms_very_low | long | Latency square sum ms very low. |
| latency_total_us | long | Latency total us. |
| latency_total_us_high | long | Latency total us high. |
| latency_total_us_low | long | Latency total us low. |
| latency_total_us_medium | long | Latency total us medium. |
| latency_total_us_moderate_high | long | Latency total us moderate high. |
| latency_total_us_very_low | long | Latency total us very low. |
| load_factor | long | Load factor. |
| lock_wait_count_per_second_max | real | Lock wait count per second max. |
| lock_wait_count_per_second_min | real | Lock wait count per second min. |
| lock_wait_time_ms_per_second_max | real | Lock wait time ms per second max. |
| lock_wait_time_ms_per_second_min | real | Lock wait time ms per second min. |
| log_bytes_accepted | long | Log size in bytes accepted. |
| log_bytes_balance | long | Log size in bytes balance. |
| log_bytes_flushed | long | Log size in bytes flushed. |
| log_bytes_generated | long | Log size in bytes generated. |
| log_bytes_non_xact | long | Log size in bytes non xact. |
| log_bytes_non_xact_critical | long | Log size in bytes non xact critical. |
| log_bytes_non_xact_critical_governed | long | Log size in bytes non xact critical governed. |
| log_bytes_non_xact_governed | long | Log size in bytes non xact governed. |
| log_bytes_overhead | long | Log size in bytes overhead. |
| log_bytes_redo_time_ms | long | Log size in bytes redo time ms in milliseconds. |
| log_bytes_redone | long | Log size in bytes redone. |
| log_bytes_used_total_per_second_max | float | Log size in bytes used total per second max. |
| log_bytes_used_total_per_second_min | float | Log size in bytes used total per second min. |
| log_commits_tracked_total_per_second_max | float | Log commits tracked total per second max. |
| log_commits_tracked_total_per_second_min | float | Log commits tracked total per second min. |
| log_current_limit | long | Log current limit. |
| log_current_wait_type | long | Type classification for log current wait. |
| log_flush_max_wait_time_ms | long | Log flush max wait time ms in milliseconds. |
| log_flush_wait_time_ms | long | Log flush wait time ms in milliseconds. |
| log_flush_waits | long | Log flush waits. |
| log_generation_max_stall_time_ms | long | Log generation max stall time ms in milliseconds. |
| log_generation_stall_time_ms | long | Log generation stall time ms in milliseconds. |
| log_generation_stalls | long | Log generation stalls. |
| log_operations_tracked_total_per_second_max | float | Log operations tracked total per second max. |
| log_operations_tracked_total_per_second_min | float | Log operations tracked total per second min. |
| log_rate_cap | long | Log rate cap. |
| log_rg_wait_time_ms | long | Log resource governor wait time ms in milliseconds. |
| log_rg_waits | long | Log resource governor waits. |
| log_temp_db_bytes_used_total_per_second_max | float | Log temp database size in bytes used total per second max. |
| log_temp_db_bytes_used_total_per_second_min | float | Log temp database size in bytes used total per second min. |
| log_time_waited_for_allotment_total_ms_per_second_max | float | Log time waited for allotment total ms per second max. |
| log_time_waited_for_allotment_total_ms_per_second_min | float | Log time waited for allotment total ms per second min. |
| log_waits_for_allotment_total_per_second_max | float | Log waits for allotment total per second max. |
| log_waits_for_allotment_total_per_second_min | float | Log waits for allotment total per second min. |
| log_writes_completed | long | Log writes completed. |
| log_writes_issued | long | Log writes issued. |
| logical_database_guid | string | Logical database guid. |
| logical_database_id | string | Logical database identifier. |
| logical_database_name | string | Logical database name. |
| logical_db_id | string | Logical database identifier. |
| logical_file_size_mb | long | Logical file size mb. |
| logical_resource_pool_name | string | Logical resource pool name. |
| login_count | long | Number of login. |
| max_cpu | real | Maximum CPU. |
| max_global_iops | long | Maximum global IOPS. |
| max_iops | long | Maximum IOPS. |
| max_log_rate | long | Maximum log rate. |
| max_log_rate_bytes_per_sec | long | Maximum log rate size in bytes per sec. |
| max_queued_iops | long | Maximum queued IOPS. |
| max_receive_bytes | long | Max receive size in bytes. |
| max_send_bytes | long | Max send size in bytes. |
| max_sessions | long | Maximum sessions. |
| max_size_mb | long | Maximum size mb. |
| max_spinlock_wait_time_ms | long | Maximum spinlock wait time ms. |
| max_tempdb_data_size_in_pages | long | Maximum tempdb data size in pages. |
| max_token_deficit_bw | long | Maximum token deficit bw. |
| max_token_deficit_io | long | Maximum token deficit I/O. |
| max_workers | long | Maximum workers. |
| memgrant_waiter_count | long | Number of memgrant waiter. |
| memgrant_waiter_count_per_second_max | float | Memgrant waiter count per second max. |
| memgrant_waiter_count_per_second_min | float | Memgrant waiter count per second min. |
| memory_cap_kb | long | Memory cap kb. |
| memory_grant_cap_kb | long | Memory grant cap kb. |
| message | string | Human-readable message text. |
| min_cpu | real | Minimum CPU. |
| min_cpu_for_violation | real | Minimum CPU for violation. |
| min_gampages_processing_per_worker | long | Minimum gampages processing per worker. |
| min_global_iops | long | Minimum global IOPS. |
| min_iops | long | Minimum IOPS. |
| min_iops_for_violation | long | Minimum IOPS for violation. |
| min_log_bytes_per_sec_for_violation | long | Minimum log size in bytes per sec for violation. |
| min_receive_bytes | long | Min receive size in bytes. |
| min_send_bytes | long | Min send size in bytes. |
| network_protocol | long | Network protocol. |
| network_protocol_component_name | string | Network protocol component name. |
| normalized_ios_completed_total_per_second_max | real | Normalized ios completed total per second max. |
| normalized_read_ios_completed_per_second_max | float | Normalized read ios completed per second max. |
| normalized_read_ios_completed_per_second_min | float | Normalized read ios completed per second min. |
| normalized_read_ios_issued_per_second_max | float | Normalized read ios issued per second max. |
| normalized_read_ios_issued_per_second_min | float | Normalized read ios issued per second min. |
| normalized_reads_completed_total_per_second_max | real | Normalized reads completed total per second max. |
| normalized_reads_completed_total_per_second_min | real | Normalized reads completed total per second min. |
| normalized_write_ios_completed_per_second_max | float | Normalized write ios completed per second max. |
| normalized_write_ios_completed_per_second_min | float | Normalized write ios completed per second min. |
| normalized_write_ios_issued_per_second_max | float | Normalized write ios issued per second max. |
| normalized_write_ios_issued_per_second_min | float | Normalized write ios issued per second min. |
| normalized_writes_completed_total_per_second_max | real | Normalized writes completed total per second max. |
| normalized_writes_completed_total_per_second_min | real | Normalized writes completed total per second min. |
| num_cores | long | Num cores. |
| num_of_bytes_read_per_second_max | float | Num of size in bytes read per second max. |
| num_of_bytes_read_per_second_min | float | Num of size in bytes read per second min. |
| num_of_bytes_written_per_second_max | float | Num of size in bytes written per second max. |
| num_of_bytes_written_per_second_min | float | Num of size in bytes written per second min. |
| num_of_reads_per_second_max | float | Num of reads per second max. |
| num_of_reads_per_second_min | float | Num of reads per second min. |
| num_of_writes_per_second_max | float | Num of writes per second max. |
| num_of_writes_per_second_min | float | Num of writes per second min. |
| num_samples | long | Num samples. |
| num_workers | long | Num workers. |
| numa_node_id | long | Numa node identifier. |
| number_of_context_switches | long | Number of context switches. |
| offline_schedulers_count | long | Number of offline schedulers. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| out_of_memory_count_per_second_max | float | Out of memory count per second max. |
| out_of_memory_count_per_second_min | float | Out of memory count per second min. |
| outbound_connection_worker_count_avg | real | Outbound connection worker count avg. |
| outbound_connection_worker_count_max | long | Outbound connection worker count max. |
| outbound_connection_workers_cap | long | Outbound connection workers cap. |
| package | string | Package. |
| pages_used | long | Pages used. |
| peak_tempdb_data_space_kb | long | Peak tempdb data space kb. |
| pending_completion_disk_io_count | long | Number of pending completion disk I/O. |
| pending_issue_disk_io_count | long | Number of pending issue disk I/O. |
| period_ms | long | Period ms in milliseconds. |
| pfs_free_space_bytes | long | Pfs free space size in bytes. |
| pfs_max_size_gb | long | Pfs max size gb. |
| pfs_min_size_gb | long | Pfs min size gb. |
| pfs_total_space_bytes | long | Pfs total space size in bytes. |
| physical_database_guid | string | Physical database guid. |
| physical_database_name | string | Physical database name. |
| physical_db_id | string | Physical database identifier. |
| pool_data | string | Pool data. |
| pool_id | long | Pool identifier. |
| pool_name | string | Pool name. |
| prev_cached_page_allocs | long | Prev cached page allocs. |
| prev_cached_page_deallocs | long | Prev cached page deallocs. |
| prev_pages_allocated_at_fullscan | long | Prev pages allocated at fullscan. |
| process_id | long | Process identifier. |
| quantum_length_us | real | Quantum length us. |
| queued_io_cap | long | Queued I/O cap. |
| read_ahead_count | long | Number of read ahead. |
| read_ahead_pages_count | long | Number of read ahead pages. |
| read_bytes_total_per_second_max | float | Read size in bytes total per second max. |
| read_bytes_total_per_second_min | float | Read size in bytes total per second min. |
| read_io_completed_total_per_second_max | float | Read I/O completed total per second max. |
| read_io_completed_total_per_second_min | float | Read I/O completed total per second min. |
| read_io_issued_total_per_second_max | float | Read I/O issued total per second max. |
| read_io_issued_total_per_second_min | float | Read I/O issued total per second min. |
| read_io_queued_total_per_second_max | float | Read I/O queued total per second max. |
| read_io_queued_total_per_second_min | float | Read I/O queued total per second min. |
| read_io_stall_queued_ms_per_second_max | float | Read I/O stall queued ms per second max. |
| read_io_stall_queued_ms_per_second_min | float | Read I/O stall queued ms per second min. |
| read_io_stall_total_ms_per_second_max | float | Read I/O stall total ms per second max. |
| read_io_stall_total_ms_per_second_min | float | Read I/O stall total ms per second min. |
| read_io_throttled_total_per_second_max | float | Read I/O throttled total per second max. |
| read_io_throttled_total_per_second_min | float | Read I/O throttled total per second min. |
| read_stall_queued_ms_per_second_max | float | Read stall queued ms per second max. |
| read_stall_queued_ms_per_second_min | float | Read stall queued ms per second min. |
| read_stall_total_ms_per_second_max | float | Read stall total ms per second max. |
| read_stall_total_ms_per_second_min | float | Read stall total ms per second min. |
| reads_completed_total_per_second_max | float | Reads completed total per second max. |
| reads_completed_total_per_second_min | float | Reads completed total per second min. |
| reads_issued_total_per_second_max | float | Reads issued total per second max. |
| reads_issued_total_per_second_min | float | Reads issued total per second min. |
| reads_queued_total_per_second_max | float | Reads queued total per second max. |
| reads_queued_total_per_second_min | float | Reads queued total per second min. |
| reads_throttled_avg | float | Reads throttled avg. |
| reads_throttled_max | long | Reads throttled max. |
| reads_throttled_per_second_max | long | Reads throttled per second max. |
| reason_of_dump | long | Reason of dump. |
| receive_bytes | long | Receive size in bytes. |
| receive_bytes_throttled | long | Receive size in bytes throttled. |
| request_cpu_cap_msec | long | Request CPU cap msec. |
| resource_name | string | Resource name. |
| root_token_bucket_depth_bw | long | Root token bucket depth bw. |
| root_token_bucket_depth_io | long | Root token bucket depth I/O. |
| root_token_bucket_fill_interval_ms | long | Root token bucket fill interval ms in milliseconds. |
| root_token_bucket_fill_rate_per_second_bw | long | Root token bucket fill rate per second bw. |
| root_token_bucket_fill_rate_per_second_io | long | Root token bucket fill rate per second I/O. |
| runnable_tasks_count | long | Number of runnable tasks. |
| scheduler_address | string | Scheduler address. |
| scheduler_id | long | Scheduler identifier. |
| send_bytes | long | Send size in bytes. |
| send_bytes_throttled | long | Send size in bytes throttled. |
| serverless_paused_state | string | State value for serverless paused. |
| sessionName | string | Session Name. |
| session_cap | long | Session cap. |
| sessions_cap | long | Sessions cap. |
| size_on_disk_bytes | long | Size on disk size in bytes. |
| size_on_disk_bytes_per_second_max | float | Size on disk size in bytes per second max. |
| size_on_disk_bytes_per_second_min | float | Size on disk size in bytes per second min. |
| snapshot_time | datetime | Snapshot time timestamp. |
| spaceused_mb | long | Spaceused mb. |
| start_aggregated_sample | datetime | Start aggregated sample. |
| start_of_first_granular_sample | datetime | Start of first granular sample. |
| statistics_start_time | datetime | Statistics start time timestamp. |
| status | string | Current status reported by the component. |
| storage_account_name | string | Storage account name. |
| storage_type | long | Type classification for storage. |
| summary_duration_ms | long | Summary duration ms in milliseconds. |
| system_thread_id | long | System thread identifier. |
| target_latency_high_us | long | Target latency high us. |
| target_latency_low_us | long | Target latency low us. |
| target_latency_very_high_us | long | Target latency very high us. |
| target_latency_very_low_us | long | Target latency very low us. |
| target_memory_kb_avg | float | Target memory kb avg. |
| target_memory_kb_max | long | Target memory kb max. |
| tempdb_data_space_kb | long | Tempdb data space kb. |
| throttled_time_ms | long | Throttled time ms in milliseconds. |
| time_taken_ms | long | Time taken ms in milliseconds. |
| time_to_collect_stats_ms_avg | float | Time to collect stats ms avg. |
| time_to_collect_stats_ms_max | long | Time to collect stats ms max. |
| total_cpu_active_ms_per_second_max | float | Total CPU active ms per second max. |
| total_cpu_active_ms_per_second_min | float | Total CPU active ms per second min. |
| total_cpu_delayed_ms_per_second_max | float | Total CPU delayed ms per second max. |
| total_cpu_delayed_ms_per_second_min | float | Total CPU delayed ms per second min. |
| total_cpu_usage_actual_ms_per_second_max | real | Total CPU usage actual ms per second max. |
| total_cpu_usage_actual_ms_per_second_min | real | Total CPU usage actual ms per second min. |
| total_cpu_usage_ms | long | Total CPU usage ms. |
| total_cpu_usage_ms_1min_per_millisecond_max | real | Total CPU usage ms 1min per millisecond max. |
| total_cpu_usage_ms_1min_per_millisecond_min | real | Total CPU usage ms 1min per millisecond min. |
| total_cpu_usage_ms_5mins_per_millisecond_max | real | Total CPU usage ms 5mins per millisecond max. |
| total_cpu_usage_ms_5mins_per_millisecond_min | real | Total CPU usage ms 5mins per millisecond min. |
| total_cpu_usage_ms_per_second_max | float | Total CPU usage ms per second max. |
| total_cpu_usage_ms_per_second_min | float | Total CPU usage ms per second min. |
| total_cpu_usage_preemptive_ms_per_second_max | float | Total CPU usage preemptive ms per second max. |
| total_cpu_usage_preemptive_ms_per_second_min | float | Total CPU usage preemptive ms per second min. |
| total_gampages | long | Total gampages. |
| total_io_count | long | Number of total I/O. |
| total_memgrant_count_per_second_max | float | Total memgrant count per second max. |
| total_memgrant_count_per_second_min | float | Total memgrant count per second min. |
| total_memgrant_timeout_count_per_second_max | float | Total memgrant timeout count per second max. |
| total_memgrant_timeout_count_per_second_min | float | Total memgrant timeout count per second min. |
| total_query_optimization_count_per_second_max | float | Total query optimization count per second max. |
| total_query_optimization_count_per_second_min | float | Total query optimization count per second min. |
| total_reduced_memgrant_count_per_second_max | float | Total reduced memgrant count per second max. |
| total_reduced_memgrant_count_per_second_min | float | Total reduced memgrant count per second min. |
| total_request_count | long | Number of total request. |
| total_request_count_per_second_max | float | Total request count per second max. |
| total_request_count_per_second_min | float | Total request count per second min. |
| total_requested_bytes | long | Total requested size in bytes. |
| total_requested_bytes_high | long | Total requested size in bytes high. |
| total_requested_bytes_low | long | Total requested size in bytes low. |
| total_requested_bytes_medium | long | Total requested size in bytes medium. |
| total_requested_bytes_moderate_high | long | Total requested size in bytes moderate high. |
| total_requested_bytes_very_low | long | Total requested size in bytes very low. |
| total_suboptimal_plan_generation_count_per_second_max | float | Total suboptimal plan generation count per second max. |
| total_suboptimal_plan_generation_count_per_second_min | float | Total suboptimal plan generation count per second min. |
| total_tempdb_data_limit_violation_count | long | Number of total tempdb data limit violation. |
| total_tempdb_statement_limit_violation_count | long | Number of total tempdb statement limit violation. |
| trigger_source | string | Trigger source. |
| type_desc | string | Type desc. |
| used_bpool_memory_kb | long | Used bpool memory kb. |
| used_bpool_memory_kb_avg | real | Used bpool memory kb avg. |
| used_bpool_memory_kb_max | long | Used bpool memory kb max. |
| used_data_space_kb_avg | float | Used data space kb avg. |
| used_data_space_kb_max | long | Used data space kb max. |
| used_memgrant_kb | long | Used memgrant kb. |
| used_memgrant_kb_avg | float | Used memgrant kb avg. |
| used_memgrant_kb_max | long | Used memgrant kb max. |
| used_memory_kb | long | Used memory kb. |
| used_memory_kb_avg | float | Used memory kb avg. |
| used_memory_kb_max | long | Used memory kb max. |
| vcpu_config_percent | real | Vcpu config percentage. |
| volume_file_count | long | Number of volume file. |
| volume_identity | string | Volume identity. |
| volume_name | string | Volume name. |
| volume_no | long | Volume no. |
| volume_outstanding_bytes | long | Volume outstanding size in bytes. |
| volume_outstanding_bytes_limit_hit | long | Volume outstanding size in bytes limit hit. |
| volume_outstanding_io | long | Volume outstanding I/O. |
| volume_outstanding_io_limit_hit | long | Volume outstanding I/O limit hit. |
| volume_type | long | Type classification for volume. |
| work_queue_count | long | Number of work queue. |
| workers_cap | long | Workers cap. |
| write_bytes_total_per_second_max | float | Write size in bytes total per second max. |
| write_bytes_total_per_second_min | float | Write size in bytes total per second min. |
| write_io_completed_total_per_second_max | float | Write I/O completed total per second max. |
| write_io_completed_total_per_second_min | float | Write I/O completed total per second min. |
| write_io_issued_total_per_second_max | float | Write I/O issued total per second max. |
| write_io_issued_total_per_second_min | float | Write I/O issued total per second min. |
| write_io_queued_total_per_second_max | float | Write I/O queued total per second max. |
| write_io_queued_total_per_second_min | float | Write I/O queued total per second min. |
| write_io_stall_queued_ms_per_second_max | float | Write I/O stall queued ms per second max. |
| write_io_stall_queued_ms_per_second_min | float | Write I/O stall queued ms per second min. |
| write_io_stall_total_ms_per_second_max | float | Write I/O stall total ms per second max. |
| write_io_stall_total_ms_per_second_min | float | Write I/O stall total ms per second min. |
| write_io_throttled_total_per_second_max | float | Write I/O throttled total per second max. |
| write_io_throttled_total_per_second_min | float | Write I/O throttled total per second min. |
| write_stall_queued_ms_per_second_max | real | Write stall queued ms per second max. |
| write_stall_queued_ms_per_second_min | real | Write stall queued ms per second min. |
| write_stall_total_ms_per_second_max | float | Write stall total ms per second max. |
| write_stall_total_ms_per_second_min | float | Write stall total ms per second min. |
| writes_completed_total_per_second_max | float | Writes completed total per second max. |
| writes_completed_total_per_second_min | float | Writes completed total per second min. |
| writes_issued_total_per_second_max | float | Writes issued total per second max. |
| writes_issued_total_per_second_min | float | Writes issued total per second min. |
| writes_queued_total_per_second_max | float | Writes queued total per second max. |
| writes_queued_total_per_second_min | float | Writes queued total per second min. |
| writes_throttled_per_second_max | long | Writes throttled per second max. |

## MonSqlSampledBufferPoolDescriptors — SQL Sampled Buffer Pool Descriptors

**Purpose**: SQL Sampled Buffer Pool Descriptors. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: performance. Often used to explain wait or latency patterns.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| allocation_unit_id | long | Allocation unit identifier. |
| attach_activity_id | string | Attach activity identifier. |
| attach_activity_id_xfer | string | Attach activity id xfer. |
| database_id | long | Database identifier. |
| event | string | Event name emitted by the component. |
| file_id | long | File identifier. |
| free_space_in_bytes | long | Free space in size in bytes. |
| is_in_bpool_extension | bool | Boolean flag indicating whether in bpool extension. |
| is_modified | bool | Boolean flag indicating whether modified. |
| logical_database_guid | string | Logical database guid. |
| numa_node | long | Numa node. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| page_id | long | Page identifier. |
| page_level | long | Page level. |
| page_type | string | Type classification for page. |
| read_microsec | long | Read microsec. |
| row_count | long | Number of row. |
| sessionName | string | Session Name. |
| tag_id | long | Tag identifier. |
| total_hashed_count | long | Number of total hashed. |
| use1_sec | long | Use1 sec. |
| use2_sec | long | Use2 sec. |

## MonWiDmDbPartitionStats — Workload insights DM Database Partition Stats

**Purpose**: Workload insights DM Database Partition Stats. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| code_package_version | string | Code package version. |
| database_id | long | Database identifier. |
| database_name | string | Database name. |
| end_utc_date | datetime | End utc date. |
| in_row_data_page_count | long | Number of in row data page. |
| in_row_reserved_page_count | long | Number of in row reserved page. |
| in_row_used_page_count | long | Number of in row used page. |
| index_id | long | Index identifier. |
| lob_reserved_page_count | long | Number of lob reserved page. |
| lob_used_page_count | long | Number of lob used page. |
| logical_database_name | string | Logical database name. |
| object_id | long | Object identifier. |
| partition_id | long | Partition identifier. |
| partition_number | long | Partition number. |
| reserved_page_count | long | Number of reserved page. |
| row_count | long | Number of row. |
| row_overflow_reserved_page_count | long | Number of row overflow reserved page. |
| row_overflow_used_page_count | long | Number of row overflow used page. |
| start_utc_date | datetime | Start utc date. |
| used_page_count | long | Number of used page. |

## MonWorkerWaitStats — Worker Wait Stats

**Purpose**: Worker Wait Stats. Used to troubleshoot CPU, memory, I/O, waits, quotas, and workload pressure on Managed Instance. Referenced in MI template areas: availability. Often used to explain wait or latency patterns. Often used to correlate SQL behavior with Service Fabric activity.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| client_pid | long | Client pid. |
| code_package_version | string | Code package version. |
| error_state | long | State value for error. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| instance_rg_size | string | Instance resource governor size. |
| logical_database_guid | string | Logical database guid. |
| logical_database_name | string | Logical database name. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| plan_handle | string | Plan handle. |
| query_hash | long | Query hash. |
| query_plan_hash | long | Query plan hash. |
| session_id | long | Session identifier. |
| text_data | string | Text data. |
| tsql_frame | string | Tsql frame. |

# 3. Availability & Failover

## MonDbSeedTraces — Seeding and replica synchronization trace

**Purpose**: Seeding and replica synchronization trace. Used to investigate outages, replica health, seeding, failover, and recovery behavior. Referenced in MI template areas: availability, backup-restore. Often used during backup or restore investigations.
**Category**: Availability

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| attach_activity_id | string | Attach activity identifier. |
| attach_activity_id_xfer | string | Attach activity id xfer. |
| code_package_version | string | Code package version. |
| compression_options | string | Compression options. |
| database_id | long | Database identifier. |
| database_name | string | Database name. |
| database_size_bytes | long | Database size size in bytes. |
| enqueue_type_node | bool | Boolean flag indicating whether enqueue type node. |
| estimated_completion_time | datetime | Estimated completion time timestamp. |
| event | string | Event name emitted by the component. |
| failure_code | long | Failure code. |
| failure_message | string | Failure message. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| internal_state_desc | string | Internal state desc. |
| is_compression_enabled | bool | Boolean flag indicating whether compression enabled. |
| local_seeding_guid | string | Local seeding guid. |
| new_state | string | State value for new. |
| old_state | string | State value for old. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| process_id | long | Process identifier. |
| remote_machine_name | string | Remote machine name. |
| remote_seeding_guid | string | Remote seeding guid. |
| retry_count | long | Number of retry. |
| role_desc | string | Role desc. |
| seeding_end_time | datetime | Seeding end time timestamp. |
| seeding_start_time | datetime | Seeding start time timestamp. |
| sessionName | string | Session Name. |
| system_thread_id | long | System thread identifier. |
| total_disk_io_wait_time_ms | long | Total disk I/O wait time ms. |
| total_network_wait_time_ms | long | Total network wait time ms. |
| transfer_rate_bytes_per_second | long | Transfer rate size in bytes per second. |
| transferred_size_bytes | long | Transferred size size in bytes. |

## MonDmContinuousCopyStatus — DM Continuous Copy Status

**Purpose**: DM Continuous Copy Status. Used to investigate outages, replica health, seeding, failover, and recovery behavior. Referenced in MI template areas: availability, backup-restore.
**Category**: Availability

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| code_package_version | string | Code package version. |
| copy_guid | string | Copy guid. |
| end_utc_date | datetime | End utc date. |
| is_interlink_connected | long | Boolean flag indicating whether interlink connected. |
| is_rpo_limit_reached | long | Boolean flag indicating whether rpo limit reached. |
| is_target_role | long | Boolean flag indicating whether target role. |
| last_replication | string | Last replication. |
| link_type | string | Type classification for link. |
| local_slo | string | Local slo. |
| partner_app | string | Partner app. |
| partner_cluster | string | Partner cluster. |
| partner_database | string | Partner database. |
| partner_node | string | Partner node. |
| partner_physical_database_id | string | Partner physical database identifier. |
| partner_replica_id | string | Partner replica identifier. |
| partner_server | string | Partner server. |
| partner_slo | string | Partner slo. |
| physical_database_id | string | Physical database identifier. |
| replication_lag_sec | string | Replication lag sec. |
| replication_state | string | State value for replication. |
| replication_state_desc | string | Replication state desc. |
| start_utc_date | datetime | Start utc date. |

## MonDmDbHadrReplicaStates — DM Database HADR Replica States

**Purpose**: DM Database HADR Replica States. Used to investigate outages, replica health, seeding, failover, and recovery behavior. Referenced in MI template areas: availability, backup-restore, networking. Often used during failover or replica troubleshooting.
**Category**: Availability

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| code_package_version | string | Code package version. |
| database_id | long | Database identifier. |
| database_state | long | State value for database. |
| database_state_desc | string | Database state desc. |
| end_of_log_lsn | string | End of log lsn. |
| end_utc_date | datetime | End utc date. |
| filestream_send_rate | long | Filestream send rate. |
| group_database_id | string | Group database identifier. |
| group_id | string | Group identifier. |
| internal_state | long | State value for internal. |
| internal_state_desc | string | Internal state desc. |
| is_commit_participant | long | Boolean flag indicating whether commit participant. |
| is_forwarder | long | Boolean flag indicating whether forwarder. |
| is_local | long | Boolean flag indicating whether local. |
| is_primary_replica | long | Boolean flag indicating whether primary replica. |
| is_seeding_in_progress | long | Boolean flag indicating whether seeding in progress. |
| is_suspended | long | Boolean flag indicating whether suspended. |
| last_commit_lsn | string | Last commit lsn. |
| last_commit_time | datetime | Last commit time timestamp. |
| last_hardened_lsn | string | Last hardened lsn. |
| last_hardened_time | datetime | Last hardened time timestamp. |
| last_received_lsn | string | Last received lsn. |
| last_received_time | datetime | Last received time timestamp. |
| last_redone_lsn | string | Last redone lsn. |
| last_redone_time | datetime | Last redone time timestamp. |
| last_sent_lsn | string | Last sent lsn. |
| last_sent_time | datetime | Last sent time timestamp. |
| log_send_queue_size | long | Log send queue size. |
| log_send_rate | long | Log send rate. |
| logical_database_name | string | Logical database name. |
| low_water_mark_for_ghosts | long | Low water mark for ghosts. |
| quorum_commit_lsn | string | Quorum commit lsn. |
| quorum_commit_time | datetime | Quorum commit time timestamp. |
| recovery_lsn | string | Recovery lsn. |
| redo_queue_size | long | Redo queue size. |
| redo_rate | long | Redo rate. |
| replica_id | string | Replica identifier. |
| secondary_lag_seconds | long | Secondary lag seconds. |
| start_utc_date | datetime | Start utc date. |
| suspend_reason | long | Suspend reason. |
| suspend_reason_desc | string | Suspend reason desc. |
| synchronization_health | long | Synchronization health. |
| synchronization_health_desc | string | Synchronization health desc. |
| synchronization_state | long | State value for synchronization. |
| synchronization_state_desc | string | Synchronization state desc. |
| truncation_lsn | string | Truncation lsn. |

## MonGeoDRFailoverGroups — Failover group configuration and role state

**Purpose**: Failover group configuration and role state. Used to investigate outages, replica health, seeding, failover, and recovery behavior. Referenced in MI template areas: availability, backup-restore. Often used during failover or replica troubleshooting. Often used during backup or restore investigations.
**Category**: Availability

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| all_servers | string | All servers. |
| code_package_version | string | Code package version. |
| end_utc_date | datetime | End utc date. |
| failover_grace_period_in_minutes | long | Failover grace period in minutes. |
| failover_group_create_time | datetime | Failover group create time timestamp. |
| failover_group_id | string | Failover group identifier. |
| failover_group_name | string | Failover group name. |
| failover_group_type | string | Type classification for failover group. |
| failover_policy | string | Failover policy. |
| failover_with_data_loss_grace_period_in_minutes | long | Failover with data loss grace period in minutes. |
| is_geo_secondary_disaster_recovery_only | long | Boolean flag indicating whether geo secondary disaster recovery only. |
| partner_region | string | Partner region. |
| partner_server_name | string | Partner server name. |
| readonly_endpoint_failover_policy | string | Readonly endpoint failover policy. |
| readonly_endpoint_target_server | string | Readonly endpoint target server. |
| role | string | Role. |
| start_utc_date | datetime | Start utc date. |
| sub_type | string | Type classification for sub. |

## MonManagedInstanceCategorizedDatabaseOutages — Managed Instance Categorized Database Outages

**Purpose**: Managed Instance Categorized Database Outages. Used to investigate outages, replica health, seeding, failover, and recovery behavior. Referenced in MI template areas: availability. Often used during failover or replica troubleshooting.
**Category**: Availability

| Column | Type | Description |
|--------|------|-------------|
| DatabasePartitionId | string | Database Partition Id. |
| Edition | string | Edition. |
| IssueEndTime | datetime | Issue End Time. |
| IssueStartTime | datetime | Issue Start Time. |
| LogicalDatabaseName | string | Logical Database Name. |
| NewPrimary | string | New Primary. |
| OldPrimary | string | Old Primary. |
| OutageEndTime | datetime | Outage End Time. |
| OutageHash | string | Outage Hash. |
| OutageReason | string | Outage Reason. |
| OutageReasonLevel1 | string | Outage Reason Level1. |
| OutageReasonLevel2 | string | Outage Reason Level2. |
| OutageReasonLevel3 | string | Outage Reason Level3. |
| OutageStartTime | datetime | Outage Start Time. |
| OutageTimeInSeconds | long | Outage Time In Seconds. |
| OutageType | string | Outage Type. |
| ServiceLevelObjective | string | Service Level Objective. |
| Version | string | Version. |

## MonManagedInstanceDatabaseOutages — Managed Instance Database Outages

**Purpose**: Managed Instance Database Outages. Used to investigate outages, replica health, seeding, failover, and recovery behavior. Referenced in MI template areas: availability.
**Category**: Availability

| Column | Type | Description |
|--------|------|-------------|
| DatabasePartitionId | string | Database Partition Id. |
| Edition | string | Edition. |
| Event | string | Event name emitted by the component. |
| IntervalEndTime | datetime | Interval End Time. |
| IntervalStartTime | datetime | Interval Start Time. |
| LogicalDatabaseName | string | Logical Database Name. |
| NewPrimary | string | New Primary. |
| OldPrimary | string | Old Primary. |
| OutageEndTime | datetime | Outage End Time. |
| OutageHash | string | Outage Hash. |
| OutageStartTime | datetime | Outage Start Time. |
| Type | string | Type. |
| Version | string | Version. |

## MonManagedServerCategorizedOutages — Managed Server Categorized Outages

**Purpose**: Managed Server Categorized Outages. Used to investigate outages, replica health, seeding, failover, and recovery behavior. Referenced in MI template areas: availability.
**Category**: Availability

| Column | Type | Description |
|--------|------|-------------|
| DatabasePartitionId | string | Database Partition Id. |
| Details | string | Details. |
| IsQuorumLoss | long | Is Quorum Loss. |
| IsRingResize | long | Is Ring Resize. |
| IsTDIIssue | long | Is TDIIssue. |
| IsXdbHostIssue | long | Is XDB Host Issue. |
| LongRedoQueueSizeInKB | long | Long Redo Queue Size In KB. |
| OutageEndTime | datetime | Outage End Time. |
| OutageHash | string | Outage Hash. |
| OutageReason | string | Outage Reason. |
| OutageStartTime | datetime | Outage Start Time. |
| OutageTimeInSeconds | long | Outage Time In Seconds. |
| PLBActivity | string | PLBActivity. |
| Type | string | Type. |
| logical_database_name | string | Logical database name. |
| service_level_objective | string | Service level objective. |

## MonRecoveryTrace — Recovery Trace

**Purpose**: Recovery Trace. Used to investigate outages, replica health, seeding, failover, and recovery behavior. Referenced in MI template areas: availability, backup-restore.
**Category**: Availability

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| MetricNamespace | string | Metric Namespace. |
| MonitoringAccount | string | Monitoring Account. |
| PartitionId | string | Partition Id. |
| actor_distance_begin_mb | long | Actor distance begin mb. |
| actor_distance_end_mb | long | Actor distance end mb. |
| actor_distance_mb | long | Actor distance mb. |
| analysis_elapsed_time_ms | long | Analysis elapsed time ms in milliseconds. |
| analysis_lsn | string | Analysis lsn. |
| analyze_lock_acquire_time_us | long | Analyze lock acquire time us. |
| analyze_record_time | long | Analyze record time timestamp. |
| associated_object_id | long | Associated object identifier. |
| attach_activity_id | string | Attach activity identifier. |
| attach_activity_id_xfer | string | Attach activity id xfer. |
| average_throughput_per_second | real | Average throughput per second. |
| average_writes_per_second | real | Average writes per second. |
| background_write_task_calls | long | Background write task calls. |
| batch_skip_redo_sum | long | Batch skip redo sum. |
| begin_lsn | string | Begin lsn. |
| by_system_task | bool | Boolean flag indicating whether by system task. |
| bytes_processed | long | Bytes processed. |
| catchup_redos | long | Catchup redos. |
| catchup_redos_wait_max_us | long | Catchup redos wait max us. |
| catchup_redos_wait_sum_us | long | Catchup redos wait sum us. |
| checkpoint_lsn | string | Checkpoint lsn. |
| checkpoint_rate_iops | real | Checkpoint rate IOPS. |
| checkpoint_rate_mb | real | Checkpoint rate mb. |
| code_package_version | string | Code package version. |
| collection_start_time | datetime | Collection start time timestamp. |
| command | string | Command. |
| complete_mgrs_recovery_time_ms | long | Complete mgrs recovery time ms in milliseconds. |
| component | string | Component. |
| context | string | Context. |
| context_switches | long | Context switches. |
| continuous_redo_log_redone_count | long | Number of continuous redo log redone. |
| coordinator_database_id | long | Coordinator database identifier. |
| correlation_id | string | Correlation identifier used across components. |
| count_buffers_processed | long | Number of count buffers processed. |
| count_buffers_processed_parallel | long | Number of count buffers processed parallel. |
| current_dirty_page_count | long | Number of current dirty page. |
| current_lsn | string | Current lsn. |
| current_oldest_page_lsn | string | Current oldest page lsn. |
| current_parallel_scan_requests | long | Current parallel scan requests. |
| current_parallel_task_count | long | Number of current parallel task. |
| current_serial_scan_requests | long | Current serial scan requests. |
| data | string | Data. |
| database_count | long | Number of database. |
| database_id | long | Database identifier. |
| database_name | string | Database name. |
| database_recovered_signalled | bool | Boolean flag indicating whether database recovered signalled. |
| database_segment_id | long | Database segment identifier. |
| database_type | string | Type classification for database. |
| db_phase | string | Database phase. |
| db_state | string | State value for database. |
| delay_count_when_flushed_sum | long | Delay count when flushed sum. |
| dependency_waits | long | Dependency waits. |
| dirty_page_count | long | Number of dirty page. |
| dirty_page_count_after_analysis | long | Dirty page count after analysis. |
| dirty_page_mgr_config | long | Dirty page mgr config. |
| dirty_page_read_time_ms | long | Dirty page read time ms in milliseconds. |
| dirty_page_target_time_ms | long | Dirty page target time ms in milliseconds. |
| dplist_lock_backoffs_per_min | long | Dplist lock backoffs per min. |
| dplist_lock_collisions_per_min | long | Dplist lock collisions per min. |
| dplist_lock_spins_per_collision | long | Dplist lock spins per collision. |
| dpt_entry_locks_acquired_sum | long | Dpt entry locks acquired sum. |
| dpt_entry_locks_wait_sum_us | long | Dpt entry locks wait sum us. |
| dpt_entry_locks_wasted_sum | long | Dpt entry locks wasted sum. |
| dpt_entry_skip_count_max | long | Dpt entry skip count max. |
| drains | long | Drains. |
| drains_max_us | long | Drains max us. |
| drains_sum_us | long | Drains sum us. |
| edition | string | Edition. |
| elapsed_time_ms | long | Elapsed time ms in milliseconds. |
| elapsed_time_sec | long | Elapsed time sec. |
| elastic_pool_db_count | long | Number of elastic pool database. |
| error_number | long | SQL or platform error number. |
| estimated_remaining_time_sec | long | Estimated remaining time sec. |
| event | string | Event name emitted by the component. |
| extra_flush_count | long | Number of extra flush. |
| findxdes_optimized_count | long | Number of findxdes optimized. |
| findxdes_unoptimized_count | long | Number of findxdes unoptimized. |
| flow_controls | long | Flow controls. |
| flow_controls_max_us | long | Flow controls max us. |
| flow_controls_sum_us | long | Flow controls sum us. |
| flushes_issued | long | Flushes issued. |
| flushes_requested | long | Flushes requested. |
| force_flush_lsn | string | Force flush lsn. |
| forced_pages | long | Forced pages. |
| forced_writes | long | Forced writes. |
| foreign_file_id | long | Foreign file identifier. |
| hbvalue_db | long | Hbvalue database. |
| hekaton_recovery_lsn | string | Hekaton recovery lsn. |
| helper_forced_pages | long | Helper forced pages. |
| helper_forced_writes | long | Helper forced writes. |
| helper_pool_current_dispatchers | long | Helper pool current dispatchers. |
| helper_pool_fading_dispatchers | long | Helper pool fading dispatchers. |
| helper_pool_ideal_dispatchers | long | Helper pool ideal dispatchers. |
| helper_pool_queue_size | long | Helper pool queue size. |
| helper_pool_timeout_ms | long | Helper pool timeout ms in milliseconds. |
| helper_skipped | long | Helper skipped. |
| helper_sleep | long | Helper sleep. |
| helper_throttle_stall_ms | long | Helper throttle stall ms in milliseconds. |
| helper_unforced_pages | long | Helper unforced pages. |
| helper_unforced_writes | long | Helper unforced writes. |
| helper_write_task_calls | long | Helper write task calls. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| ignored_flush_count | long | Number of ignored flush. |
| init_pvs_time_ms | long | Init pvs time ms in milliseconds. |
| initalize_for_scans_time_ms | long | Initalize for scans time ms in milliseconds. |
| internal_slo_name | string | Internal slo name. |
| interval | long | Interval. |
| interval_time | long | Interval time timestamp. |
| io_saturation | long | I/O saturation. |
| io_throttle_scheme | string | I/O throttle scheme. |
| io_throttle_stall_ms | long | I/O throttle stall ms in milliseconds. |
| io_throttle_stalls | long | I/O throttle stalls. |
| is_acceptlog_mode | bool | Boolean flag indicating whether acceptlog mode. |
| is_adr_enabled | bool | Boolean flag indicating whether adr enabled. |
| is_batch_redo_enabled | bool | Boolean flag indicating whether batch redo enabled. |
| is_dynamic | long | Boolean flag indicating whether dynamic. |
| is_elastic_pool_db | bool | Boolean flag indicating whether elastic pool database. |
| is_foreign | bool | Boolean flag indicating whether foreign. |
| is_in_online_single_thread_pool_mode | bool | Boolean flag indicating whether in online single thread pool mode. |
| is_long_checkpoint | bool | Boolean flag indicating whether long checkpoint. |
| is_parallel_redo | bool | Boolean flag indicating whether parallel redo. |
| is_parallel_redo_enabled | bool | Boolean flag indicating whether parallel redo enabled. |
| is_primary_replica | bool | Boolean flag indicating whether primary replica. |
| is_torn_affinity | string | Boolean flag indicating whether torn affinity. |
| last_checkpoint_lsn | string | Last checkpoint lsn. |
| last_lsn | string | Last lsn. |
| last_oldest_page_lsn | string | Last oldest page lsn. |
| local_page_check_sum | long | Local page check sum. |
| lock_acquire_time_us | long | Lock acquire time us. |
| lockspace_nest_id | long | Lockspace nest identifier. |
| lockspace_sub_id | long | Lockspace sub identifier. |
| lockspace_workspace_id | string | Lockspace workspace identifier. |
| log_blocks_blocking_reads | long | Log blocks blocking reads. |
| log_blocks_cache_misses | long | Log blocks cache misses. |
| log_blocks_consumed | long | Log blocks consumed. |
| log_bytes_consumed | long | Log size in bytes consumed. |
| log_consumed | long | Log consumed. |
| log_op | string | Log op. |
| log_op_details | long | Log op details. |
| log_produced | long | Log produced. |
| log_record_time | long | Log record time timestamp. |
| logical_database_guid | string | Logical database guid. |
| logical_db_id | string | Logical database identifier. |
| logical_db_name | string | Logical database name. |
| logs_redone_sum | long | Logs redone sum. |
| master_xdes_id_high | long | Master xdes id high. |
| master_xdes_id_low | long | Master xdes id low. |
| max_delay_count_processed | long | Maximum delay count processed. |
| max_delayed_page_work_item_list_size | long | Maximum delayed page work item list size. |
| max_fix_time_page_id | long | Max fix time page identifier. |
| max_lsn | string | Maximum lsn. |
| max_page_fix_time_us | long | Maximum page fix time us. |
| max_page_limit | long | Maximum page limit. |
| max_page_work_item_list_size | long | Maximum page work item list size. |
| max_parallel_task_count | long | Number of max parallel task. |
| max_redo_page_id | long | Max redo page identifier. |
| max_time_us | long | Maximum time us. |
| min_delayed_page_work_item_list_size | long | Minimum delayed page work item list size. |
| min_lsn | string | Minimum lsn. |
| min_time_us | long | Minimum time us. |
| mode | string | Mode. |
| new_page_work_items_allocated_count | long | Number of new page work items allocated. |
| object_id | long | Object identifier. |
| oldest_page_lsn | string | Oldest page lsn. |
| opcode | string | Opcode. |
| operation | string | Operation. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| owner_type | string | Type classification for owner. |
| package | string | Package. |
| page_fix_total_us | long | Page fix total us. |
| page_ref_latch_acquire_sum | long | Page ref latch acquire sum. |
| page_work_items_initialized_count | long | Number of page work items initialized. |
| page_writes_logged | long | Page writes logged. |
| page_writes_not_logged | long | Page writes not logged. |
| pages_written | long | Pages written. |
| parallel_tasks | long | Parallel tasks. |
| participant_database_id | long | Participant database identifier. |
| percent_complete | long | Percent complete. |
| phase | string | Phase. |
| physical_db_id | string | Physical database identifier. |
| physical_db_name | string | Physical database name. |
| process_id | long | Process identifier. |
| read_ahead_bpool_hit_count | long | Number of read ahead bpool hit. |
| read_ahead_hashmap_hit_count | long | Number of read ahead hashmap hit. |
| read_ahead_hashmap_reset_caused_by_hashmapfull_count | long | Number of read ahead hashmap reset caused by hashmapfull. |
| read_ahead_hashmap_reset_caused_by_timer_count | long | Number of read ahead hashmap reset caused by timer. |
| read_ahead_hashmap_reset_max_time_ms | long | Read ahead hashmap reset max time ms in milliseconds. |
| read_ahead_hashmap_reset_min_time_ms | long | Read ahead hashmap reset min time ms in milliseconds. |
| read_ahead_hashmap_reset_sum_cost_ms | long | Read ahead hashmap reset sum cost ms in milliseconds. |
| read_ahead_pages_attempted_to_prefetch_count | long | Number of read ahead pages attempted to prefetch. |
| read_ahead_rbiodb_cost_sum_ms | long | Read ahead rbiodb cost sum ms in milliseconds. |
| read_ahead_rbpex_commit_cost_sum_ms | long | Read ahead rbpex commit cost sum ms in milliseconds. |
| read_ahead_rbpex_haspage_cost_sum_ms | long | Read ahead rbpex haspage cost sum ms in milliseconds. |
| read_ahead_rbpex_haspage_found_hit_count | long | Number of read ahead rbpex haspage found hit. |
| read_ahead_rbpex_haspage_not_found_hit_count | long | Number of read ahead rbpex haspage not found hit. |
| read_ahead_rbpex_init_cost_sum_ms | long | Read ahead rbpex init cost sum ms in milliseconds. |
| read_ahead_rbpex_missing_count | long | Number of read ahead rbpex missing. |
| read_ahead_rbpex_tx_failed_count | long | Number of read ahead rbpex tx failed. |
| read_ahead_read_issued_sum_ms | long | Read ahead read issued sum ms in milliseconds. |
| read_ahead_wait_no_read_issued_sum_ms | long | Read ahead wait no read issued sum ms in milliseconds. |
| recovery_data_read_time_estimate_ms | long | Recovery data read time estimate ms in milliseconds. |
| recovery_log_bytes | long | Recovery log size in bytes. |
| recovery_log_read_time_estimate_ms | long | Recovery log read time estimate ms in milliseconds. |
| recovery_log_target_time_ms | long | Recovery log target time ms in milliseconds. |
| recovery_stage | string | Recovery stage. |
| recovery_step | string | Recovery step. |
| recovery_time | long | Recovery time timestamp. |
| recovery_time_estimate_sec | long | Recovery time estimate sec. |
| recovery_writer_group_queued_ios | long | Recovery writer group queued ios. |
| redo_active_time_count | long | Number of redo active time. |
| redo_call_stack | string | Redo call stack. |
| redo_elapsed_time_ms | long | Redo elapsed time ms in milliseconds. |
| redo_end_lsn | string | Redo end lsn. |
| redo_kill_blocked_iteration | long | Redo kill blocked iteration. |
| redo_maximum_active_time | long | Redo maximum active time timestamp. |
| redo_maximum_read_time | long | Redo maximum read time timestamp. |
| redo_misses | long | Redo misses. |
| redo_page_fixes | long | Redo page fixes. |
| redo_pool_current_dispatchers | long | Redo pool current dispatchers. |
| redo_pool_fading_dispatchers | long | Redo pool fading dispatchers. |
| redo_pool_ideal_dispatchers | long | Redo pool ideal dispatchers. |
| redo_pool_queue_size | long | Redo pool queue size. |
| redo_pool_timeout_ms | long | Redo pool timeout ms in milliseconds. |
| redo_read_ms | long | Redo read ms in milliseconds. |
| redo_read_time_count | long | Number of redo read time. |
| redo_start_lsn | string | Redo start lsn. |
| redo_thread_active_time | long | Redo thread active time timestamp. |
| redo_thread_read_time | long | Redo thread read time timestamp. |
| redo_thread_stall_time | long | Redo thread stall time timestamp. |
| redo_wait_time_local_disk_io_ms | long | Redo wait time local disk I/O ms in milliseconds. |
| redo_wait_time_ms | long | Redo wait time ms in milliseconds. |
| redo_wait_time_remote_read_io_ms | long | Redo wait time remote read I/O ms in milliseconds. |
| redo_waits | long | Redo waits. |
| redo_wasted_reads | long | Redo wasted reads. |
| redone_count | long | Number of redone. |
| redone_total_us | long | Redone total us. |
| redundant_flush_count | long | Number of redundant flush. |
| refresh_boot_page_fields_time_ms | long | Refresh boot page fields time ms in milliseconds. |
| regular_undo_elapsed_time_ms | long | Regular undo elapsed time ms in milliseconds. |
| replica_role | string | Replica role. |
| replica_write_status | string | Status value for replica write. |
| report_period_millisecs | long | Report period millisecs. |
| resource_0 | long | Resource 0. |
| resource_1 | long | Resource 1. |
| resource_2 | long | Resource 2. |
| resource_description | string | Resource description. |
| resource_type | string | Type classification for resource. |
| safe_enqueues_to_threadpool | long | Safe enqueues to threadpool. |
| scan_dropped_alloc_unit_after_recovery_time_ms | long | Scan dropped alloc unit after recovery time ms in milliseconds. |
| scanned_buffers | long | Scanned buffers. |
| service_name | string | Service name. |
| sessionName | string | Session Name. |
| skip_redo_sum | long | Skip redo sum. |
| skipped_dpt_entry_redone_sum | long | Skipped dpt entry redone sum. |
| skipped_dpt_entry_sum | long | Skipped dpt entry sum. |
| slog_redone_count | long | Number of slog redone. |
| slog_redone_total_us | long | Slog redone total us. |
| started_redo_workers | long | Started redo workers. |
| state | string | Current lifecycle or health state. |
| successful_flush_count | long | Number of successful flush. |
| system_thread_id | long | System thread identifier. |
| system_undo_elapsed_time_ms | long | System undo elapsed time ms in milliseconds. |
| target_log_bytes | long | Target log size in bytes. |
| target_lsn | string | Target lsn. |
| target_recovery_time_sec | long | Target recovery time sec. |
| total_buffers | long | Total buffers. |
| total_elapsed_time_sec | long | Total elapsed time sec. |
| total_iterated_buffers | long | Total iterated buffers. |
| total_parallel_scan_requests | long | Total parallel scan requests. |
| total_restrained_scan_requests | long | Total restrained scan requests. |
| total_scan_requests | long | Total scan requests. |
| total_serial_scan_requests | long | Total serial scan requests. |
| total_should_flush_calls | long | Total should flush calls. |
| total_writes | long | Total writes. |
| trace_message | string | Trace message. |
| transaction_id | string | Transaction identifier. |
| transaction_outcome | bool | Boolean flag indicating whether transaction outcome. |
| undo_elapsed_time_ms | long | Undo elapsed time ms in milliseconds. |
| undo_logical_revert_xacts_time_ms | long | Undo logical revert xacts time ms in milliseconds. |
| unforced_pages | long | Unforced pages. |
| unforced_write_miss_percent | long | Unforced write miss percentage. |
| unforced_writes | long | Unforced writes. |
| version_cleaner_throttle_stall_ms | long | Version cleaner throttle stall ms in milliseconds. |
| version_cleaner_unforced_pages | long | Version cleaner unforced pages. |
| version_cleaner_unforced_writes | long | Version cleaner unforced writes. |
| version_cleaner_write_task_calls | long | Version cleaner write task calls. |
| wait_time_ms | long | Wait time in milliseconds. |
| wait_time_seconds | long | Wait time seconds. |
| wasted_flush_count | long | Number of wasted flush. |
| work_items_delayed_count | long | Number of work items delayed. |
| work_items_flushed_count | long | Number of work items flushed. |
| work_items_skipped_count | long | Number of work items skipped. |
| worker_thread_id | long | Worker thread identifier. |
| xact_outcome_count | long | Number of xact outcome. |
| xdes_id_high | long | Xdes id high. |
| xdes_id_low | long | Xdes id low. |

## MonSsbManagedInstanceTransmissions — Service Broker Managed Instance Transmissions

**Purpose**: Service Broker Managed Instance Transmissions. Used to investigate outages, replica health, seeding, failover, and recovery behavior. Referenced in MI template areas: availability.
**Category**: Availability

| Column | Type | Description |
|--------|------|-------------|
| code_package_version | string | Code package version. |
| conversation_handle | string | Conversation handle. |
| database_id | long | Database identifier. |
| database_name | string | Database name. |
| end_utc_date | datetime | End utc date. |
| endpoint_conversation_id | string | Endpoint conversation identifier. |
| endpoint_state | string | State value for endpoint. |
| endpoint_state_desc | string | Endpoint state desc. |
| is_conversation_error | long | Boolean flag indicating whether conversation error. |
| logical_database_name | string | Logical database name. |
| priority | long | Priority. |
| start_utc_date | datetime | Start utc date. |
| to_broker_instance | string | To broker instance. |

## MonXdbLaunchSetup — XDB Launch Setup

**Purpose**: XDB Launch Setup. Used to investigate outages, replica health, seeding, failover, and recovery behavior. Referenced in MI template areas: availability.
**Category**: Availability

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| OneBoxClusterId | string | One Box Cluster Id. |
| PartitionId | string | Partition Id. |
| component | string | Component. |
| event | string | Event name emitted by the component. |
| message | string | Human-readable message text. |
| message_systemmetadata | string | Message systemmetadata. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| process_id | long | Process identifier. |
| sessionName | string | Session Name. |
| severity | string | Severity level associated with the event. |
| version | string | Version. |

# 4. Backup & Restore

## MonBackup — Backup operation history

**Purpose**: Backup operation history. Used to troubleshoot backup generation, retention, snapshot growth, and restore execution. Referenced in MI template areas: backup-restore, performance. Often used during backup or restore investigations.
**Category**: Backup

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| TridentServerType | string | Trident Server Type. |
| additional_request_details | string | Additional request details. |
| alert_type | string | Type classification for alert. |
| api_name | string | Api name. |
| auth_type | string | Type classification for auth. |
| availability_group_id | string | Availability group identifier. |
| azure_storage_client_request_id | string | Azure storage client request identifier. |
| azure_storage_service_request_id | string | Azure storage service request identifier. |
| backend_session | bool | Boolean flag indicating whether backend session. |
| backup_account_name | string | Backup account name. |
| backup_end_date | string | Backup end date. |
| backup_parameter_strategy | string | Backup parameter strategy. |
| backup_path | string | Backup path. |
| backup_relative_path | string | Backup relative path. |
| backup_service_state | string | State value for backup service. |
| backup_set_guid | string | Backup set guid. |
| backup_size | string | Backup size. |
| backup_start_date | string | Backup start date. |
| backup_storage_redundancy | string | Backup storage redundancy. |
| backup_time | string | Backup timestamp associated with the record. |
| backup_to_nul | bool | Boolean flag indicating whether backup to nul. |
| backup_type | string | Type classification for backup. |
| begin_time | string | Begin time timestamp. |
| blocksize_in_bytes | string | Blocksize in size in bytes. |
| br_details | string | Br details. |
| br_error_details | string | Br error details. |
| br_error_type | string | Type classification for br error. |
| br_exception_message | string | Br exception message. |
| br_exception_stack_trace | string | Br exception stack trace. |
| buffer_count | long | Number of buffer. |
| cleanup_event_status | string | Status value for cleanup event. |
| cleanup_event_type | string | Type classification for cleanup event. |
| client_class | string | Client class. |
| cloud_blob_type | string | Type classification for cloud blob. |
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| compression | bool | Boolean flag indicating whether compression. |
| compression_options | string | Compression options. |
| configuration_name | string | Configuration name. |
| configuration_section_name | string | Configuration section name. |
| configuration_value | string | Configuration value. |
| connectionString | string | Connection String. |
| continue_after_error | bool | Boolean flag indicating whether continue after error. |
| database_backup_lsn | string | Database backup lsn. |
| database_id | long | Database identifier. |
| database_name | string | Database name. |
| db_read_size_in_bytes | string | Database read size in size in bytes. |
| details | string | Details. |
| device_count | long | Number of device. |
| differential_base_guid | string | Differential base guid. |
| differential_base_lsn | string | Differential base lsn. |
| elapsed_time_milliseconds | real | Elapsed duration in milliseconds. |
| event | string | Event name emitted by the component. |
| event_source | string | Event source. |
| event_type | string | Type classification for event. |
| exception | string | Exception. |
| exception_details | string | Exception details. |
| exception_details_scrubbed | string | Exception details scrubbed. |
| exception_message | string | Exception message. |
| exception_stack | string | Exception stack. |
| exception_stack_trace | string | Exception stack trace. |
| execution_time_ms | long | Execution time ms in milliseconds. |
| file_count | string | Number of file. |
| file_name | string | File name. |
| file_size_in_bytes | string | File size in size in bytes. |
| first_lsn | string | First lsn. |
| is_damaged | string | Boolean flag indicating whether damaged. |
| iteration_count | long | Number of iteration. |
| iteration_status | string | Status value for iteration. |
| iteration_time_in_seconds | string | Iteration time in seconds. |
| last_log_backup_attempted_time | string | Last log backup attempted time timestamp. |
| last_lsn | string | Last lsn. |
| last_valid_restore_time | string | Last valid restore time timestamp. |
| log_held_up_mb | real | Log held up mb. |
| log_max_size_mb | real | Log max size mb. |
| logical_database_id | string | Logical database identifier. |
| logical_database_name | string | Logical database name. |
| ltr_container_name | string | LTR container name. |
| ltr_container_resource_id | string | LTR container resource identifier. |
| ltr_data_source_id | string | LTR data source identifier. |
| ltr_recovery_point_id | string | LTR recovery point identifier. |
| max_transfer_size | string | Maximum transfer size. |
| message_type | string | Type classification for message. |
| network_server_time_ms | long | Network server time ms in milliseconds. |
| number_of_databases_enqueued | long | Number of databases enqueued. |
| number_of_databases_skipped | long | Number of databases skipped. |
| number_of_full_backups_taken | long | Number of full backups taken. |
| number_of_log_backups_taken | long | Number of log backups taken. |
| number_of_pending_full_backups | long | Number of pending full backups. |
| number_of_pending_log_backups | long | Number of pending log backups. |
| number_of_running_full_backups | long | Number of running full backups. |
| number_of_running_log_backups | long | Number of running log backups. |
| number_of_skipped_log_backups | long | Number of skipped log backups. |
| number_of_stripes | long | Number of stripes. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| parameters_with_scrubbed_values_object_name | string | Parameters with scrubbed values object name. |
| parameters_with_scrubbed_values_resource_name | string | Parameters with scrubbed values resource name. |
| parameters_with_scrubbed_values_systemmetadata | string | Parameters with scrubbed values systemmetadata. |
| physical_database_id | string | Physical database identifier. |
| physical_database_name | string | Physical database name. |
| process_id | long | Process identifier. |
| progress_event_type | string | Type classification for progress event. |
| query_api_name | string | Query api name. |
| query_parameters | string | Query parameters. |
| query_result | string | Query result. |
| recovery_fork_guid | string | Recovery fork guid. |
| relocation_count | long | Number of relocation. |
| request_id | string | Request identifier used to correlate the operation. |
| request_result | string | Request result. |
| restore_request_id | string | Restore request identifier. |
| server_name | string | Managed Instance server name. |
| sessionName | string | Session Name. |
| session_id | long | Session identifier. |
| skip_dek_initialization_during_backup | bool | Boolean flag indicating whether skip dek initialization during backup. |
| skipped_backup_reason | string | Skipped backup reason. |
| sql_error_message | string | SQL error message. |
| sql_error_number | long | SQL error number. |
| sql_error_severity | long | SQL error severity. |
| sql_error_state | long | State value for SQL error. |
| sql_query | string | SQL query. |
| stats_mask | long | Stats mask. |
| storage_container_url | string | Storage container url. |
| target_replica_id | string | Target replica identifier. |
| time_taken_in_milliseconds | string | Time taken in in milliseconds. |
| transaction_id | long | Transaction identifier. |
| transaction_log_reserved_kb | long | Transaction log reserved kb. |
| transaction_log_usage_kb | long | Transaction log usage kb. |
| uncompressed_backup_size | string | Uncompressed backup size. |
| uri | string | Uri. |
| using_dynamic_parameterss | bool | Boolean flag indicating whether using dynamic parameterss. |
| value_option_mask | long | Value option mask. |
| vlf_sequence_number | long | Vlf sequence number. |

## MonBillingBackupDatabaseSize — Billing Backup Database Size

**Purpose**: Billing Backup Database Size. Used to troubleshoot backup generation, retention, snapshot growth, and restore execution. Referenced in MI template areas: general. Often used for sizing or billing-related investigations. Often used during backup or restore investigations.
**Category**: Backup

| Column | Type | Description |
|--------|------|-------------|
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| correlation_id | string | Correlation identifier used across components. |
| event | string | Event name emitted by the component. |
| execution_time_msec | long | Execution time msec. |
| file_type | string | Type classification for file. |
| logical_database_id | string | Logical database identifier. |
| logical_server_id | string | Logical server identifier. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| physical_database_name | string | Physical database name. |
| process_id | long | Process identifier. |
| sessionName | string | Session Name. |
| size_bytes | string | Size measured in bytes. |

## MonBillingGeoSnapshotSize — Billing Geo Snapshot Size

**Purpose**: Billing Geo Snapshot Size. Used to troubleshoot backup generation, retention, snapshot growth, and restore execution. Referenced in MI template areas: general. Often used for sizing or billing-related investigations.
**Category**: Backup

| Column | Type | Description |
|--------|------|-------------|
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| correlation_id | string | Correlation identifier used across components. |
| event | string | Event name emitted by the component. |
| execution_time_msec | long | Execution time msec. |
| file_type | string | Type classification for file. |
| logical_database_id | string | Logical database identifier. |
| logical_server_id | string | Logical server identifier. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| physical_database_name | string | Physical database name. |
| process_id | long | Process identifier. |
| sessionName | string | Session Name. |
| size_bytes | string | Size measured in bytes. |

## MonBillingSnapshotSize — Billing Snapshot Size

**Purpose**: Billing Snapshot Size. Used to troubleshoot backup generation, retention, snapshot growth, and restore execution. Referenced in MI template areas: general. Often used for sizing or billing-related investigations. Often used during backup or restore investigations.
**Category**: Backup

| Column | Type | Description |
|--------|------|-------------|
| backup_time | datetime | Backup timestamp associated with the record. |
| backup_type | string | Type classification for backup. |
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| correlation_id | string | Correlation identifier used across components. |
| event | string | Event name emitted by the component. |
| execution_time_msec | long | Execution time msec. |
| file_type | string | Type classification for file. |
| logical_database_id | string | Logical database identifier. |
| logical_server_id | string | Logical server identifier. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| physical_database_name | string | Physical database name. |
| process_id | long | Process identifier. |
| sessionName | string | Session Name. |
| size_bytes | string | Size measured in bytes. |

## MonCDCTraces — CDCTraces

**Purpose**: CDCTraces. Used to troubleshoot backup generation, retention, snapshot growth, and restore execution. Referenced in MI template areas: backup-restore. Often used during backup or restore investigations.
**Category**: Backup

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppName_cdc_db_enable | string | App Name CDC database enable. |
| AppName_cdc_error | string | App Name CDC error. |
| AppName_cdc_session | string | App Name CDC session. |
| AppTypeName_Ex | string | App Type Name Ex. |
| AppTypeName_cdc_db_enable | string | App Type Name CDC database enable. |
| AppTypeName_cdc_error | string | App Type Name CDC error. |
| AppTypeName_cdc_session | string | App Type Name CDC session. |
| PartitionId | string | Partition Id. |
| attach_activity_id | string | Attach activity identifier. |
| attach_activity_id_xfer | string | Attach activity id xfer. |
| begin_lsn | string | Begin lsn. |
| change_table_delete_count | long | Number of change table delete. |
| change_table_id | long | Change table identifier. |
| cleanup_error | long | Cleanup error. |
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| command_count | long | Number of command. |
| component | string | Component. |
| current_lsn | string | Current lsn. |
| database_id | long | Database identifier. |
| duration | long | Duration. |
| empty_scan_count | long | Number of empty scan. |
| enabled | bool | Boolean flag indicating whether enabled. |
| end_lsn | string | End lsn. |
| end_time | datetime | End timestamp. |
| entry_time | datetime | Entry time timestamp. |
| error_count | long | Number of error. |
| error_message | string | Error message. |
| error_number | long | SQL or platform error number. |
| error_severity | long | Error severity. |
| error_state | long | State value for error. |
| event | string | Event name emitted by the component. |
| event_details | string | Event details. |
| event_type | string | Type classification for event. |
| failed_sessions_count | long | Number of failed sessions. |
| first_begin_cdc_lsn | string | First begin CDC lsn. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| job_id | string | Job identifier. |
| job_parameters | string | Job parameters. |
| job_type | string | Type classification for job. |
| last_commit_cdc_lsn | string | Last commit CDC lsn. |
| last_commit_cdc_time | datetime | Last commit CDC time timestamp. |
| last_commit_lsn | string | Last commit lsn. |
| last_commit_time | datetime | Last commit time timestamp. |
| latency | long | Latency. |
| log_record_count | long | Number of log record. |
| logical_database_guid | string | Logical database guid. |
| logical_database_id | string | Logical database identifier. |
| logical_database_name | string | Logical database name. |
| low_water_mark | string | Low water mark. |
| lsn_time_mapping_delete_count | long | Number of lsn time mapping delete. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| phase_number | long | Phase number. |
| physical_database_guid | string | Physical database guid. |
| retention | long | Retention. |
| schema_change_count | long | Number of schema change. |
| sequence_value | string | Sequence value. |
| sessionName | string | Session Name. |
| session_id | long | Session identifier. |
| spid | long | Spid. |
| start_lsn | string | Start lsn. |
| start_time | datetime | Start timestamp. |
| status | long | Current status reported by the component. |
| threshold | long | Threshold. |
| tran_count | long | Number of tran. |

## MonCTTraces — CTTraces

**Purpose**: CTTraces. Used to troubleshoot backup generation, retention, snapshot growth, and restore execution. Referenced in MI template areas: backup-restore.
**Category**: Backup

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppName_change_tracking_cleanup | string | App Name change tracking cleanup. |
| AppName_committable_persist_info | string | App Name committable persist info. |
| AppName_committable_recovery_info | string | App Name committable recovery info. |
| AppName_syscommittab_cleanup | string | App Name syscommittab cleanup. |
| AppTypeName_Ex | string | App Type Name Ex. |
| AppTypeName_change_tracking_cleanup | string | App Type Name change tracking cleanup. |
| AppTypeName_committable_persist_info | string | App Type Name committable persist info. |
| AppTypeName_committable_recovery_info | string | App Type Name committable recovery info. |
| AppTypeName_syscommittab_cleanup | string | App Type Name syscommittab cleanup. |
| CleanupLatencySec | string | Cleanup Latency Sec. |
| PartitionId | string | Partition Id. |
| attach_activity_id | string | Attach activity identifier. |
| attach_activity_id_xfer | string | Attach activity id xfer. |
| auto_cleanup_guid | string | Auto cleanup guid. |
| bootpage_new_commit_ts | long | Bootpage new commit ts. |
| bootpage_old_commit_ts | long | Bootpage old commit ts. |
| checkpoint_ts | long | Checkpoint ts. |
| cleaned_upto_date | datetime | Cleaned upto date. |
| cleanup_id | string | Cleanup identifier. |
| cleanup_ts | long | Cleanup ts. |
| code_package_version | string | Code package version. |
| commit_ts | long | Commit ts. |
| commit_ts_adjustment_needed | bool | Boolean flag indicating whether commit ts adjustment needed. |
| commit_ts_persisted | bool | Boolean flag indicating whether commit ts persisted. |
| commit_ts_to_be_persisted | bool | Boolean flag indicating whether commit ts to be persisted. |
| current_ts | long | Current ts. |
| database_id | long | Database identifier. |
| event | string | Event name emitted by the component. |
| flush_commit_ts | long | Flush commit ts. |
| hard_flush | bool | Boolean flag indicating whether hard flush. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| logical_database_guid | string | Logical database guid. |
| logical_database_name | string | Logical database name. |
| message | string | Human-readable message text. |
| mode | string | Mode. |
| object_id | long | Object identifier. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| persist_new | bool | Boolean flag indicating whether persist new. |
| physical_database_guid | string | Physical database guid. |
| recovery_ts | long | Recovery ts. |
| recovery_ts_persisted | long | Recovery ts persisted. |
| row_count | long | Number of row. |
| rows_deleted | long | Rows deleted. |
| rows_in_delay | long | Rows in delay. |
| sessionName | string | Session Name. |
| startup_ts | long | Startup ts. |
| status | long | Current status reported by the component. |
| value | string | Value. |

## MonFulltextActiveCatalogs — Fulltext Active Catalogs

**Purpose**: Fulltext Active Catalogs. Used to troubleshoot backup generation, retention, snapshot growth, and restore execution. Referenced in MI template areas: backup-restore.
**Category**: Backup

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| active_fts_index_count | long | Number of active fts index. |
| auto_population_count | long | Number of auto population. |
| catalog_id | long | Catalog identifier. |
| change_tracking_state_desc | string | Change tracking state desc. |
| code_package_version | string | Code package version. |
| crawl_end_date | datetime | Crawl end date. |
| crawl_start_date | datetime | Crawl start date. |
| crawl_type_desc | string | Crawl type desc. |
| data_space_id | long | Data space identifier. |
| database_id | long | Database identifier. |
| docs_processed | long | Docs processed. |
| end_utc_date | datetime | End utc date. |
| fail_count | long | Number of fail. |
| full_incremental_population_count | long | Number of full incremental population. |
| has_crawl_completed | long | Boolean flag indicating whether crawl completed. |
| incremental_timestamp | string | Incremental timestamp. |
| index_version | long | Index version. |
| is_enabled | long | Boolean flag indicating whether enabled. |
| is_importing | long | Boolean flag indicating whether importing. |
| is_paused | long | Boolean flag indicating whether paused. |
| item_count | long | Number of item. |
| key_column | long | Key column. |
| manual_population_count | long | Number of manual population. |
| memory_address | string | Memory address. |
| merge_status | long | Status value for merge. |
| name | string | Object or resource name. |
| object_id | long | Object identifier. |
| pending_changes | long | Pending changes. |
| populate_status | long | Status value for populate. |
| previous_status | long | Status value for previous. |
| previous_status_description | string | Previous status description. |
| property_list_id | long | Property list identifier. |
| row_count_in_thousands | long | Row count in thousands. |
| start_utc_date | datetime | Start utc date. |
| status | long | Current status reported by the component. |
| status_description | string | Status description. |
| stoplist_id | long | Stoplist identifier. |
| unique_index_id | long | Unique index identifier. |
| worker_count | long | Number of worker. |

## MonFullTextInfo — Full Text Info

**Purpose**: Full Text Info. Used to troubleshoot backup generation, retention, snapshot growth, and restore execution. Referenced in MI template areas: backup-restore. Often used during backup or restore investigations.
**Category**: Backup

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| code_package_version | string | Code package version. |
| crawl_operation | string | Crawl operation. |
| database_id | long | Database identifier. |
| database_name | string | Database name. |
| degree_of_parallelism | long | Degree of parallelism. |
| destination_fragment_id | long | Destination fragment identifier. |
| destination_partition_count | long | Number of destination partition. |
| error_number | long | SQL or platform error number. |
| event | string | Event name emitted by the component. |
| filter_count | long | Number of filter. |
| filter_type | string | Type classification for filter. |
| fragment_id | long | Fragment identifier. |
| fragments_count | long | Number of fragments. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| language_count | long | Number of language. |
| lcid | long | Lcid. |
| logical_database_guid | string | Logical database guid. |
| logical_database_name | string | Logical database name. |
| max_input_size | long | Maximum input size. |
| max_output_size | long | Maximum output size. |
| message | string | Human-readable message text. |
| min_input_size | long | Minimum input size. |
| min_output_size | long | Minimum output size. |
| object_id | long | Object identifier. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| physical_database_guid | string | Physical database guid. |
| sessionName | string | Session Name. |
| table_id | long | Table identifier. |
| table_name | string | Table name. |
| table_object_id | long | Table object identifier. |
| total_fragments_size | long | Total fragments size. |

## MonImportExport — Import Export

**Purpose**: Import Export. Used to troubleshoot backup generation, retention, snapshot growth, and restore execution. Referenced in MI template areas: backup-restore.
**Category**: Backup

| Column | Type | Description |
|--------|------|-------------|
| Detail | string | Detail. |
| ExceptionErrorClassification | string | Exception Error Classification. |
| ExceptionMessage | string | Exception Message. |
| ExceptionStackTrace | string | Exception Stack Trace. |
| ExceptionType | string | Exception Type. |
| Level | string | Level. |
| LogicalDatabaseName | string | Logical Database Name. |
| Progress | string | Progress. |
| additional_request_details | string | Additional request details. |
| api_name | string | Api name. |
| auth_type | string | Type classification for auth. |
| azure_storage_client_request_id | string | Azure storage client request identifier. |
| azure_storage_service_request_id | string | Azure storage service request identifier. |
| client_class | string | Client class. |
| cloud_blob_type | string | Type classification for cloud blob. |
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| elapsed_time_milliseconds | real | Elapsed duration in milliseconds. |
| event | string | Event name emitted by the component. |
| exception | string | Exception. |
| exception_message | string | Exception message. |
| exception_type | string | Type classification for exception. |
| fabric_cluster_name | string | Fabric cluster name. |
| fabric_name_uri | string | Fabric name uri. |
| fabric_property_name | string | Fabric property name. |
| operation_id | string | Operation identifier for the workflow. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| parameters_with_scrubbed_values_object_name | string | Parameters with scrubbed values object name. |
| parameters_with_scrubbed_values_resource_name | string | Parameters with scrubbed values resource name. |
| parameters_with_scrubbed_values_systemmetadata | string | Parameters with scrubbed values systemmetadata. |
| process_id | long | Process identifier. |
| property_name | string | Property name. |
| request_id | string | Request identifier used to correlate the operation. |
| request_result | string | Request result. |
| sessionName | string | Session Name. |
| stack_trace | string | Stack trace. |
| uri | string | Uri. |

## MonLogReaderTraces — Log Reader Traces

**Purpose**: Log Reader Traces. Used to troubleshoot backup generation, retention, snapshot growth, and restore execution. Referenced in MI template areas: backup-restore. Often used during backup or restore investigations.
**Category**: Backup

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| TridentServerType | string | Trident Server Type. |
| aggregate_log_accumulation_bps | long | Aggregate log accumulation bps. |
| articles_completed | long | Articles completed. |
| attach_activity_id | string | Attach activity identifier. |
| attach_activity_id_xfer | string | Attach activity id xfer. |
| cache_quota | long | Cache quota. |
| clear_size | long | Clear size. |
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| command_count | long | Number of command. |
| compensation_log_record_bytes | long | Compensation log record size in bytes. |
| compensation_log_record_count | long | Number of compensation log record. |
| compensation_ranges_count | long | Number of compensation ranges. |
| consumer_id | long | Consumer identifier. |
| consumer_name | string | Consumer name. |
| current_lsn | string | Current lsn. |
| database_id | long | Database identifier. |
| dist_backup_lsn | string | Dist backup lsn. |
| dist_last_lsn | string | Dist last lsn. |
| end_lsn | string | End lsn. |
| eol_lsn | string | Eol lsn. |
| event | string | Event name emitted by the component. |
| first_begin_cdc_lsn | string | First begin CDC lsn. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| last_commit_cdc_lsn | string | Last commit CDC lsn. |
| last_commit_lsn | string | Last commit lsn. |
| last_replicated_tx_latency_sec | real | Last replicated tx latency sec. |
| log_full_percent_from_repl | real | Log full percentage from repl. |
| log_pool_miss_count | long | Number of log pool miss. |
| log_pool_miss_rate_pct | real | Log pool miss rate pct. |
| log_record_count | long | Number of log record. |
| log_scan_function | string | Log scan function. |
| log_scan_size_bytes | long | Log scan size size in bytes. |
| log_size_remaining_bytes | long | Log size remaining size in bytes. |
| logical_database_guid | string | Logical database guid. |
| logical_database_name | string | Logical database name. |
| logpool_total_read_count | long | Number of logpool total read. |
| lower_bound_max_trans | long | Lower bound max trans. |
| max_trans | long | Maximum trans. |
| newest_lsn | string | Newest lsn. |
| next_lsn | string | Next lsn. |
| numtrans | long | Numtrans. |
| oldest_lsn | string | Oldest lsn. |
| originalEventTimestamp | string | Original Event timestamp. |
| output_max_trans | long | Output max trans. |
| package | string | Package. |
| phase_number | long | Phase number. |
| phase_state | long | State value for phase. |
| phase_state_name | string | Phase state name. |
| physical_database_guid | string | Physical database guid. |
| pool_trunc_lsn | string | Pool trunc lsn. |
| prev_max_trans | long | Prev max trans. |
| prev_phase2_scan_termination_reason | string | Prev phase2 scan termination reason. |
| prev_tran_count | long | Number of prev tran. |
| read_ahead_cnt | long | Read ahead cnt. |
| repl_begin_lsn | string | Repl begin lsn. |
| repl_next_lsn | string | Repl next lsn. |
| repl_timer_perf_parameters_in_ticks | string | Repl timer perf parameters in ticks. |
| repldone_failure_code | string | Repldone failure code. |
| repldone_phase | long | Repldone phase. |
| repldone_phase_name | string | Repldone phase name. |
| reset | long | Reset. |
| scheduler_id_at_end | long | Scheduler id at end. |
| scheduler_id_at_start | long | Scheduler id at start. |
| schema_change_count | long | Number of schema change. |
| sessionName | string | Session Name. |
| session_id | long | Session identifier. |
| shared_pool_size | long | Shared pool size. |
| start_lsn | string | Start lsn. |
| start_time | string | Start timestamp. |
| tail_log_cache_miss_count | long | Number of tail log cache miss. |
| time | datetime | Time. |
| total_read_count | long | Number of total read. |
| tracked_begin_lsn | string | Tracked begin lsn. |
| tracked_next_lsn | string | Tracked next lsn. |
| tracking_boundary_lsn | string | Tracking boundary lsn. |
| tran_completed | long | Tran completed. |
| tran_count | long | Number of tran. |
| upper_bound_log_runway_max_trans | long | Upper bound log runway max trans. |
| upper_bound_max_trans | long | Upper bound max trans. |
| wait_stats | string | Wait stats. |
| worker_migration_count_at_end | long | Worker migration count at end. |
| worker_migration_count_at_start | long | Worker migration count at start. |
| xact_id | string | Xact identifier. |
| xact_seqno | string | Xact seqno. |

## MonLtrConfiguration — LTR Configuration

**Purpose**: LTR Configuration. Used to troubleshoot backup generation, retention, snapshot growth, and restore execution. Referenced in MI template areas: backup-restore.
**Category**: Backup

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| code_package_version | string | Code package version. |
| create_time | datetime | Creation timestamp. |
| customer_subscription_id | string | Customer subscription identifier. |
| db_created_time | datetime | Database created time timestamp. |
| db_dropped_time | datetime | Database dropped time timestamp. |
| end_utc_date | datetime | End utc date. |
| first_backup_time | datetime | First backup time timestamp. |
| first_time_use_versioning_account | datetime | First time use versioning account. |
| immutability_policy_mode | string | Immutability policy mode. |
| is_billable | long | Boolean flag indicating whether billable. |
| is_geodr_secondary | long | Boolean flag indicating whether geodr secondary. |
| is_vldb | long | Boolean flag indicating whether vldb. |
| last_backup_time | datetime | Last backup time timestamp. |
| last_policy_change_time | datetime | Last policy change time timestamp. |
| last_process_time | datetime | Last process time timestamp. |
| logical_database_id | string | Logical database identifier. |
| logical_database_name | string | Logical database name. |
| logical_server_id | string | Logical server identifier. |
| make_backups_immutable | long | Make backups immutable. |
| max_retention_in_days | long | Maximum retention in days. |
| monthly_retention | string | Monthly retention. |
| next_backup_time | datetime | Next backup time timestamp. |
| num_backups | long | Num backups. |
| server_type | string | Type classification for server. |
| start_utc_date | datetime | Start utc date. |
| state | string | Current lifecycle or health state. |
| week_of_year | long | Week of year. |
| weekly_retention | string | Weekly retention. |
| yearly_retention | string | Yearly retention. |

## MonManagementArchivedBackup — Management Archived Backup

**Purpose**: Management Archived Backup. Used to troubleshoot backup generation, retention, snapshot growth, and restore execution. Referenced in MI template areas: backup-restore. Often used during backup or restore investigations.
**Category**: Backup

| Column | Type | Description |
|--------|------|-------------|
| archived_backup_resource_id | string | Archived backup resource identifier. |
| backup_time | string | Backup timestamp associated with the record. |
| br_error_details | string | Br error details. |
| br_error_type | string | Type classification for br error. |
| br_exception_message | string | Br exception message. |
| br_exception_stack_trace | string | Br exception stack trace. |
| client_address | string | Client address. |
| correlation_id | string | Correlation identifier used across components. |
| current_locked_expire_date | datetime | Current locked expire date. |
| details | string | Details. |
| elapsed_time | string | Elapsed duration for the operation. |
| elapsed_time_in_milliseconds | real | Elapsed time in in milliseconds. |
| error_message | string | Error message. |
| event | string | Event name emitted by the component. |
| event_source | string | Event source. |
| exception | string | Exception. |
| exception_message | string | Exception message. |
| exception_type | string | Type classification for exception. |
| failureCount | long | Failure Count. |
| failure_type | string | Type classification for failure. |
| level | string | Level. |
| logical_database_id | string | Logical database identifier. |
| logical_database_name | string | Logical database name. |
| logical_server_id | string | Logical server identifier. |
| message | string | Human-readable message text. |
| message_type | string | Type classification for message. |
| monthly_retention | string | Monthly retention. |
| new_locked_expire_date | datetime | New locked expire date. |
| operation | string | Operation. |
| operation_name | string | Operation name. |
| operation_type | string | Type classification for operation. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| physical_database_name | string | Physical database name. |
| progress_message_scrubbed | string | Progress message scrubbed. |
| query_text | string | Query text. |
| recovery_service_vault_container_name | string | Recovery service vault container name. |
| recovery_service_vault_name | string | Recovery service vault name. |
| recovery_service_vault_policy_name | string | Recovery service vault policy name. |
| recovery_service_vault_protected_item_name | string | Recovery service vault protected item name. |
| request_id | string | Request identifier used to correlate the operation. |
| request_url | string | Request url. |
| resource_group_name | string | Resource group name. |
| response_content | string | Response content. |
| response_length | long | Response length. |
| retention_policy_name | string | Retention policy name. |
| retry_count | long | Number of retry. |
| sessionName | string | Session Name. |
| stack_trace | string | Stack trace. |
| status_code | string | Status code. |
| storage_account_name | string | Storage account name. |
| storage_account_subscription_id | string | Storage account subscription identifier. |
| storage_container_name | string | Storage container name. |
| success_count | long | Number of success. |
| tenant_id | string | Tenant identifier. |
| vault_name | string | Vault name. |
| vault_resource_group_name | string | Vault resource group name. |
| vault_subscription_id | string | Vault subscription identifier. |
| week_of_year | string | Week of year. |
| weekly_retention | string | Weekly retention. |
| yearly_retention | string | Yearly retention. |

## MonRestoreEvents — Restore Events

**Purpose**: Restore Events. Used to troubleshoot backup generation, retention, snapshot growth, and restore execution. Referenced in MI template areas: backup-restore.
**Category**: Backup

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| TridentServerType | string | Trident Server Type. |
| additional_request_details | string | Additional request details. |
| api_name | string | Api name. |
| auth_type | string | Type classification for auth. |
| azure_storage_client_request_id | string | Azure storage client request identifier. |
| azure_storage_service_request_id | string | Azure storage service request identifier. |
| backend_session | bool | Boolean flag indicating whether backend session. |
| backup_file_name | string | Backup file name. |
| block_size | long | Block size. |
| br_error_details | string | Br error details. |
| br_error_type | string | Type classification for br error. |
| br_exception_message | string | Br exception message. |
| br_exception_stack_trace | string | Br exception stack trace. |
| buffer_count | long | Number of buffer. |
| checkpoint_lsn | string | Checkpoint lsn. |
| client_class | string | Client class. |
| cloud_blob_type | string | Type classification for cloud blob. |
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| compatibility_level | string | Compatibility level. |
| compressed_backup_size | string | Compressed backup size. |
| database_backup_lsn | string | Database backup lsn. |
| database_name | string | Database name. |
| details | string | Details. |
| details_with_customer_data | string | Details with customer data. |
| device_count | long | Number of device. |
| differential_base_lsn | string | Differential base lsn. |
| elapsed_time | string | Elapsed duration for the operation. |
| elapsed_time_milliseconds | real | Elapsed duration in milliseconds. |
| event | string | Event name emitted by the component. |
| event_source | string | Event source. |
| exception | string | Exception. |
| exception_message | string | Exception message. |
| exception_stack | string | Exception stack. |
| exception_type | string | Type classification for exception. |
| execution_time_ms | long | Execution time ms in milliseconds. |
| fabricUri | string | Fabric Uri. |
| file_count | long | Number of file. |
| first_lsn | string | First lsn. |
| last_lsn | string | Last lsn. |
| level | string | Level. |
| logical_database_guid | string | Logical database guid. |
| logical_database_id | string | Logical database identifier. |
| logical_database_name | string | Logical database name. |
| max_transfer_size | long | Maximum transfer size. |
| message | string | Human-readable message text. |
| message_type | string | Type classification for message. |
| network_server_time_ms | long | Network server time ms in milliseconds. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| page_count | long | Number of page. |
| parameters_with_scrubbed_values_object_name | string | Parameters with scrubbed values object name. |
| parameters_with_scrubbed_values_resource_name | string | Parameters with scrubbed values resource name. |
| parameters_with_scrubbed_values_systemmetadata | string | Parameters with scrubbed values systemmetadata. |
| physical_database_name | string | Physical database name. |
| process_id | long | Process identifier. |
| query_api_name | string | Query api name. |
| query_parameters | string | Query parameters. |
| query_result | string | Query result. |
| query_text | string | Query text. |
| relocation_count | long | Number of relocation. |
| request_id | string | Request identifier used to correlate the operation. |
| request_result | string | Request result. |
| restore_configuration_info | string | Restore configuration info. |
| restore_database_progress | string | Restore database progress. |
| restore_database_result | string | Restore database result. |
| restore_eta | string | Restore eta. |
| restore_progress_percentage | long | Restore progress pe percentage. |
| restore_recovery_end_time | string | Restore recovery end time timestamp. |
| restore_recovery_start_time | string | Restore recovery start time timestamp. |
| restore_request_id | string | Restore request identifier. |
| restore_start_time | string | Restore start time timestamp. |
| sessionName | string | Session Name. |
| software_vendor_id | string | Software vendor identifier. |
| software_version_build | string | Software version build. |
| software_version_major | string | Software version major. |
| software_version_minor | string | Software version minor. |
| sql_error_message | string | SQL error message. |
| sql_error_number | long | SQL error number. |
| sql_error_severity | long | SQL error severity. |
| sql_error_state | long | State value for SQL error. |
| sql_instance_name | string | SQL instance name. |
| stack_trace | string | Stack trace. |
| stats_interval | long | Stats interval. |
| stats_mask | long | Stats mask. |
| uncompressed_backup_size | string | Uncompressed backup size. |
| uri | string | Uri. |
| value_option_mask | long | Value option mask. |

## MonRestoreRequests — Restore Requests

**Purpose**: Restore Requests. Used to troubleshoot backup generation, retention, snapshot growth, and restore execution. Referenced in MI template areas: backup-restore.
**Category**: Backup

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| archived_backup_resource_id | string | Archived backup resource identifier. |
| code_package_version | string | Code package version. |
| end_time | datetime | End timestamp. |
| end_utc_date | datetime | End utc date. |
| error_code | long | Numeric error code for the failure or event. |
| error_message | string | Error message. |
| error_severity | long | Error severity. |
| operation_details | string | Operation details. |
| operation_request_id | string | Operation request identifier. |
| operation_type | string | Type classification for operation. |
| point_in_time | datetime | Point in time timestamp. |
| restore_request_id | string | Restore request identifier. |
| restore_type | string | Type classification for restore. |
| source_database_dropped_time | datetime | Source database dropped time timestamp. |
| source_edition | string | Source edition. |
| source_logical_database_id | string | Source logical database identifier. |
| source_logical_database_name | string | Source logical database name. |
| source_logical_server_name | string | Source logical server name. |
| source_managed_database_dropped_time | datetime | Source managed database dropped time timestamp. |
| source_managed_database_name | string | Source managed database name. |
| source_managed_server_name | string | Source managed server name. |
| start_time | datetime | Start timestamp. |
| start_utc_date | datetime | Start utc date. |
| state | string | Current lifecycle or health state. |
| target_edition | string | Target edition. |
| target_logical_database_name | string | Target logical database name. |
| target_logical_server_name | string | Target logical server name. |
| target_managed_database_name | string | Target managed database name. |
| target_managed_server_name | string | Target managed server name. |

## MonSqlRenzoCp — SQL Renzo Cp

**Purpose**: SQL Renzo Cp. Used to troubleshoot backup generation, retention, snapshot growth, and restore execution. Referenced in MI template areas: backup-restore.
**Category**: Backup

| Column | Type | Description |
|--------|------|-------------|
| activity_id | string | Activity identifier. |
| activity_kind | string | Activity kind. |
| authentication_phase | string | Authentication phase. |
| certificate_issuer | string | Certificate issuer. |
| certificate_not_after | datetime | Certificate not after. |
| certificate_not_before | datetime | Certificate not before. |
| certificate_source | string | Certificate source. |
| certificate_subject | string | Certificate subject. |
| certificate_thumbprint | string | Certificate thumbprint. |
| chosen_certificate_thumbprint | string | Chosen certificate thumbprint. |
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| component | string | Component. |
| dac_message_type | string | Type classification for dac message. |
| dac_number | long | Dac number. |
| dac_prefix | string | Dac prefix. |
| deployment_message | string | Deployment message. |
| display_name | string | Display name. |
| duration_milliseconds | long | Duration in milliseconds. |
| elapsed_time_milliseconds | real | Elapsed duration in milliseconds. |
| endpoints | string | Endpoints. |
| event | string | Event name emitted by the component. |
| exception_message | string | Exception message. |
| exception_type | string | Type classification for exception. |
| invalid_certificate_thumbprint | string | Invalid certificate thumbprint. |
| is_success | bool | Boolean flag indicating whether success. |
| message | string | Human-readable message text. |
| message_format | string | Message format. |
| message_id | string | Message identifier. |
| message_level | string | Message level. |
| message_system | string | Message system. |
| operation_status | string | Status value for operation. |
| ordinal | long | Ordinal. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| parent_activity_id | string | Parent activity identifier. |
| port | long | Port. |
| probe_user | string | Probe user. |
| process_id | long | Process identifier. |
| progress_message | string | Progress message. |
| progress_operation_id | long | Progress operation identifier. |
| purpose | string | Purpose. |
| request_id | string | Request identifier used to correlate the operation. |
| script | string | Script. |
| service_instance_name | string | Service instance name. |
| sessionName | string | Session Name. |
| stack_trace | string | Stack trace. |
| table_name | string | Table name. |
| tags | string | Tags. |
| thumbprints | string | Thumbprints. |
| trace_id | string | Trace identifier. |

## MonSqlRenzoTraceEvent — SQL Renzo Trace Event

**Purpose**: SQL Renzo Trace Event. Used to troubleshoot backup generation, retention, snapshot growth, and restore execution. Referenced in MI template areas: backup-restore.
**Category**: Backup

| Column | Type | Description |
|--------|------|-------------|
| activityId | string | Activity Id. |
| activityName | string | Activity Name. |
| activityVector | string | Activity Vector. |
| applicationName | string | Application Name. |
| assemblyVersion | string | Assembly Version. |
| correlationId | string | Correlation Id. |
| customDimensions | string | Custom Dimensions. |
| env_time | datetime | Env time timestamp. |
| eventId | long | Event Id. |
| eventName | string | Event Name. |
| eventType | string | Event Type. |
| logSourceName | string | Log Source Name. |
| message | string | Human-readable message text. |
| pid | long | Pid. |
| serviceName | string | Service Name. |
| serviceRequestId | string | Service Request Id. |
| tid | long | Tid. |
| traceLevel | string | Trace Level. |

## MonTranReplTraces — Tran Repl Traces

**Purpose**: Tran Repl Traces. Used to troubleshoot backup generation, retention, snapshot growth, and restore execution. Referenced in MI template areas: backup-restore. Often used during backup or restore investigations.
**Category**: Backup

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| action | string | Action. |
| agent_id | long | Agent identifier. |
| attach_activity_id | string | Attach activity identifier. |
| attach_activity_id_xfer | string | Attach activity id xfer. |
| average_commands | long | Average commands. |
| average_delivery_latency | long | Average delivery latency. |
| average_delivery_rate | real | Average delivery rate. |
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| command_id | long | Command identifier. |
| comments | string | Comments. |
| context | string | Context. |
| db_id | long | Database identifier. |
| delivered_commands | long | Delivered commands. |
| delivered_transactions | long | Delivered transactions. |
| delivery_latency | long | Delivery latency. |
| delivery_rate | real | Delivery rate. |
| delivery_time | long | Delivery time timestamp. |
| description | string | Description. |
| details | string | Details. |
| dispatcher_error_type | string | Type classification for dispatcher error. |
| distributor | string | Distributor. |
| distributor_build_number | long | Distributor build number. |
| distributor_major_version | long | Distributor major version. |
| distributor_minor_version | long | Distributor minor version. |
| duration | long | Duration. |
| error_code | string | Numeric error code for the failure or event. |
| error_id | long | Error identifier. |
| error_text | string | Error text. |
| event | string | Event name emitted by the component. |
| exception_message | string | Exception message. |
| exception_stack_trace | string | Exception stack trace. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| id | long | identifier. |
| info_message | string | Info message. |
| info_type | string | Type classification for info. |
| logical_database_guid | string | Logical database guid. |
| logical_database_name | string | Logical database name. |
| message_type | string | Type classification for message. |
| metadata | string | Metadata. |
| num_bytes_since_last_event | long | Num size in bytes since last event. |
| num_cmds_per_sec | float | Num cmds per sec. |
| num_cmds_since_last_event | long | Num cmds since last event. |
| num_trans_per_sec | float | Num trans per sec. |
| num_trans_since_last_event | long | Num trans since last event. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| process_id | long | Process identifier. |
| publication | string | Publication. |
| publication_database | string | Publication database. |
| publication_id | long | Publication identifier. |
| publisher | string | Publisher. |
| repl_agent_type | string | Type classification for repl agent. |
| return_code | long | Return code. |
| runstatus | long | Runstatus. |
| sessionName | string | Session Name. |
| source_name | string | Source name. |
| start_time | datetime | Start timestamp. |
| sync_status | long | Status value for sync. |
| sync_summary | string | Sync summary. |
| time | datetime | Time. |
| total_delivered_commands | long | Total delivered commands. |
| total_idle_time | long | Total idle time timestamp. |
| total_num_bytes | long | Total num size in bytes. |
| total_num_cmds | long | Total num cmds. |
| total_num_trans | long | Total num trans. |
| total_run_time | long | Total run time timestamp. |
| total_skipped_cmds | long | Total skipped cmds. |
| total_work_time | long | Total work time timestamp. |
| xact_seqno | string | Xact seqno. |

# 5. Connectivity & Login

## MonFedAuthTicketService — Fed Auth Ticket Service

**Purpose**: Fed Auth Ticket Service. Used to analyze connection establishment, routing, authentication, and client access failures. Referenced in MI template areas: networking.
**Category**: Networking

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| aad_retry_attempts | long | Azure AD retry attempts. |
| auth_metadata_lookup_mode | long | Auth metadata lookup mode. |
| code_package_version | string | Code package version. |
| connection_type | long | Type classification for connection. |
| context_cache_insert | long | Context cache insert. |
| context_cache_lookup | long | Context cache lookup. |
| context_info | string | Context info. |
| correlation_id | string | Correlation identifier used across components. |
| database_name | string | Database name. |
| error_code | long | Numeric error code for the failure or event. |
| error_message | string | Error message. |
| error_state | long | State value for error. |
| event | string | Event name emitted by the component. |
| external_group_expansion_required | bool | Boolean flag indicating whether external group expansion required. |
| fedauth_adal_workflow | long | Fedauth adal workflow. |
| fedauth_library_type | long | Type classification for fedauth library. |
| graph_call_with_obo | bool | Boolean flag indicating whether graph call with obo. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| if_cleanup_attempted | bool | Boolean flag indicating whether if cleanup attempted. |
| is_mwc_system | bool | Boolean flag indicating whether mwc system. |
| is_mwc_user | bool | Boolean flag indicating whether mwc user. |
| is_pooled_connection | bool | Boolean flag indicating whether pooled connection. |
| logical_database_guid | string | Logical database guid. |
| logical_database_name | string | Logical database name. |
| new_timeout_value | long | New timeout value. |
| no_cleared_entries | long | No cleared entries. |
| no_expired_active_entries | long | No expired active entries. |
| no_failed_allocations | long | No failed allocations. |
| no_failed_cleanups | long | No failed cleanups. |
| no_total_entries_before_cleanup | long | No total entries before cleanup. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| result_state | long | State value for result. |
| sessionName | string | Session Name. |
| session_id | long | Session identifier. |
| sql_connection_id | string | SQL connection identifier. |
| token_validity | long | Token validity. |
| validation_is_mwc_token | bool | Boolean flag indicating whether validation mwc token. |
| validation_service_type | long | Type classification for validation service. |

## MonLinkedServerInfo — Linked Server Info

**Purpose**: Linked Server Info. Used to analyze connection establishment, routing, authentication, and client access failures. Referenced in MI template areas: networking.
**Category**: Networking

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| code_package_version | string | Code package version. |
| event | string | Event name emitted by the component. |
| external_auth_mode | long | External auth mode. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| hresult | long | Hresult. |
| is_nt_login | bool | Boolean flag indicating whether nt login. |
| is_use_self | bool | Boolean flag indicating whether use self. |
| linked_server_name | string | Linked server name. |
| logical_database_guid | string | Logical database guid. |
| logical_database_name | string | Logical database name. |
| message | string | Human-readable message text. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| provider_clsid | string | Provider clsid. |
| provider_name | string | Provider name. |
| sessionName | string | Session Name. |
| session_id | long | Session identifier. |

## MonLogin — Login and authentication activity

**Purpose**: Login and authentication activity. Used to analyze connection establishment, routing, authentication, and client access failures. Referenced in MI template areas: availability, general, networking, performance. Often used to inspect login failures or access patterns.
**Category**: Networking

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| ClientGWDecryptBytes | long | Client GWDecrypt Bytes. |
| ClientGWDecryptCalls | long | Client GWDecrypt Calls. |
| ClientGWEncryptBytes | long | Client GWEncrypt Bytes. |
| ClientGWEncryptCalls | long | Client GWEncrypt Calls. |
| GWSQLDecryptBytes | long | GWSQLDecrypt Bytes. |
| GWSQLDecryptCalls | long | GWSQLDecrypt Calls. |
| GWSQLEncryptBytes | long | GWSQLEncrypt Bytes. |
| GWSQLEncryptCalls | long | GWSQLEncrypt Calls. |
| Level | long | Level. |
| Name | string | Object or resource name. |
| OneBoxClusterId | string | One Box Cluster Id. |
| OpenConnsAdd | long | Open Conns Add. |
| OpenConnsRmv | long | Open Conns Rmv. |
| PartitionId | string | Partition Id. |
| Pid | long | Pid. |
| ProxySessionCounter | long | Proxy Session Counter. |
| RegionName | string | Region Name. |
| ResourcePoolName | string | Resource Pool Name. |
| SslHanshakeEnd | long | Ssl Hanshake End. |
| SslHanshakeStart | long | Ssl Hanshake Start. |
| StoredProcedureInvocations | long | Stored Procedure Invocations. |
| StoredProcedureName | string | Stored Procedure Name. |
| TCPAcceptAsync | long | TCPAccept Async. |
| TCPAcceptDone | long | TCPAccept Done. |
| TCPNew | long | TCPNew. |
| TCPRelease | long | TCPRelease. |
| Tid | long | Tid. |
| Timestamp | string | timestamp. |
| XODBCOpen | long | XODBCOpen. |
| XODBC_Direct_total_failed | long | XODBC Direct total failed. |
| XODBC_Direct_total_failed_ms | long | XODBC Direct total failed ms in milliseconds. |
| XODBC_Direct_total_open | long | XODBC Direct total open. |
| XODBC_Direct_total_success | long | XODBC Direct total success. |
| XODBC_Direct_total_success_ms | long | XODBC Direct total success ms in milliseconds. |
| XODBC_total_failed | long | XODBC total failed. |
| XODBC_total_failed_ms | long | XODBC total failed ms in milliseconds. |
| XODBC_total_open | long | XODBC total open. |
| XODBC_total_open_ms | long | XODBC total open ms in milliseconds. |
| _name | string | Name. |
| aclchk_status | long | Status value for aclchk. |
| action | string | Action. |
| activation_time_ms | long | Activation time ms in milliseconds. |
| activation_timeout | long | Activation timeout. |
| activation_timeout_enabled | bool | Boolean flag indicating whether activation timeout enabled. |
| alias | string | Alias. |
| alias_name | string | Alias name. |
| alias_response | string | Alias response. |
| allocations_failed | long | Allocations failed. |
| application_name | string | Application name. |
| attach_activity_id | string | Attach activity identifier. |
| azure_internal_id | string | Azure internal identifier. |
| batch_drain_complete | bool | Boolean flag indicating whether batch drain complete. |
| batch_id | long | Batch identifier. |
| batch_state | string | State value for batch. |
| body | string | Body. |
| bucket_1 | long | Bucket 1. |
| bucket_10 | long | Bucket 10. |
| bucket_11 | long | Bucket 11. |
| bucket_12 | long | Bucket 12. |
| bucket_13 | long | Bucket 13. |
| bucket_14 | long | Bucket 14. |
| bucket_15 | long | Bucket 15. |
| bucket_16 | long | Bucket 16. |
| bucket_2 | long | Bucket 2. |
| bucket_3 | long | Bucket 3. |
| bucket_4 | long | Bucket 4. |
| bucket_5 | long | Bucket 5. |
| bucket_6 | long | Bucket 6. |
| bucket_7 | long | Bucket 7. |
| bucket_8 | long | Bucket 8. |
| bucket_9 | long | Bucket 9. |
| buffer_size | long | Buffer size. |
| bytes_read | long | Bytes read. |
| bytes_written | long | Bytes written. |
| cache_type | string | Type classification for cache. |
| cache_version | long | Cache version. |
| call_stack | string | Call stack. |
| cert_name | string | Cert name. |
| cert_thumbprint_new | string | Cert thumbprint new. |
| cert_thumbprint_previous | string | Cert thumbprint previous. |
| client_connection_id | string | Client connection identifier. |
| client_pid | long | Client pid. |
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| colmetadatavarflags | long | Colmetadatavarflags. |
| concurrent_logins | long | Concurrent logins. |
| conn_dup_result | long | Conn dup result. |
| connection_address | string | Connection address. |
| connection_id | string | Connection identifier. |
| connection_peer_id | string | Connection peer identifier. |
| connection_string | string | Connection string. |
| connection_type | string | Type classification for connection. |
| cons_buffer_size | long | Cons buffer size. |
| contained_authentication_time_ms | long | Contained authentication time ms in milliseconds. |
| context_info | string | Context info. |
| control_ring_address | string | Control ring address. |
| copy_error | long | Copy error. |
| database_firewall_rules_time_ms | long | Database firewall rules time ms in milliseconds. |
| database_name | string | Database name. |
| default_timeout | long | Default timeout. |
| dispatcher_pool_size | long | Dispatcher pool size. |
| dosguard_check_time_ms | long | Dosguard check time ms in milliseconds. |
| driver_name | string | Driver name. |
| driver_version | long | Driver version. |
| driver_version_minor | long | Driver version minor. |
| duration | long | Duration. |
| duration_in_ms | long | Duration in ms in milliseconds. |
| ecl | long | Ecl. |
| encryption_options | long | Encryption options. |
| enqueue_time_ms | long | Enqueue time ms in milliseconds. |
| error | long | Error text captured for the event or operation. |
| error_code | long | Numeric error code for the failure or event. |
| error_detail | string | Error detail. |
| error_message | string | Error message. |
| error_number | long | SQL or platform error number. |
| event | string | Event name emitted by the component. |
| event_type | string | Type classification for event. |
| exec_classifier_ms | long | Exec classifier ms in milliseconds. |
| execution_time_ms | long | Execution time ms in milliseconds. |
| external_governance_policy_authorization | string | External governance policy authorization. |
| extra_info | string | Extra info. |
| fabric_alias_uri | string | Fabric alias uri. |
| fabric_instance_uri | string | Fabric instance uri. |
| fabric_node_name | string | Fabric node name. |
| failure_reason | string | Failure reason. |
| fedauth_adal_workflow | int | Fedauth adal workflow. |
| fedauth_context_build_time_ms | long | Fedauth context build time ms in milliseconds. |
| fedauth_fetch_signingkey_refresh_time_ms | long | Fedauth fetch signingkey refresh time ms in milliseconds. |
| fedauth_group_expansion_time_ms | long | Fedauth group expansion time ms in milliseconds. |
| fedauth_jwt_token_parsing_time_ms | long | Fedauth jwt token parsing time ms in milliseconds. |
| fedauth_library_type | int | Type classification for fedauth library. |
| fedauth_signature_validation_time_ms | long | Fedauth signature validation time ms in milliseconds. |
| fedauth_token_process_time_ms | long | Fedauth token process time ms in milliseconds. |
| fedauth_token_wait_time_ms | long | Fedauth token wait time ms in milliseconds. |
| federated_users_count | long | Number of federated users. |
| find_login_ms | long | Find login ms in milliseconds. |
| fingerprint_calc_status | long | Status value for fingerprint calc. |
| fingerprint_info | string | Fingerprint info. |
| firewall_cache_rules_count | long | Number of firewall cache rules. |
| firewall_lookup_result | long | Firewall lookup result. |
| firewall_rules_count | long | Number of firewall rules. |
| firewall_sys_table_rules_count | long | Number of firewall sys table rules. |
| force_refresh_status | long | Status value for force refresh. |
| force_refresh_throttle_root_cause | string | Force refresh throttle root cause. |
| global_hashtable_entry_count | long | Number of global hashtable entry. |
| global_opentask_count | long | Number of global opentask. |
| host_name | string | Host name. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| hresult | long | Hresult. |
| id | long | identifier. |
| in_quorum_catchup | bool | Boolean flag indicating whether in quorum catchup. |
| instance_name | string | Instance name. |
| instance_port | long | Instance port. |
| interface_endpoint_name | string | Interface endpoint name. |
| ipv4_firewall_cache_rules_count | long | Number of ipv4 firewall cache rules. |
| ipv4_firewall_sys_table_rules_count | long | Number of ipv4 firewall sys table rules. |
| ipv6_firewall_cache_rules_count | long | Number of ipv6 firewall cache rules. |
| ipv6_firewall_sys_table_rules_count | long | Number of ipv6 firewall sys table rules. |
| is_allow_all_rule_blocked | bool | Boolean flag indicating whether allow all rule blocked. |
| is_allowed | bool | Boolean flag indicating whether allowed. |
| is_azure_ip | bool | Boolean flag indicating whether azure ip. |
| is_client | bool | Boolean flag indicating whether client. |
| is_contained_user | bool | Boolean flag indicating whether contained user. |
| is_database_in_nsp | bool | Boolean flag indicating whether database in nsp. |
| is_database_level_rule | bool | Boolean flag indicating whether database level rule. |
| is_duplicated | bool | Boolean flag indicating whether duplicated. |
| is_expired | bool | Boolean flag indicating whether expired. |
| is_external_authentication_only | bool | Boolean flag indicating whether external authentication only. |
| is_failoverpartner_token_returned | bool | Boolean flag indicating whether failoverpartner token returned. |
| is_first_party_customer | bool | Boolean flag indicating whether first party customer. |
| is_ipv4_mapped_ipv6_address | bool | Boolean flag indicating whether ipv4 mapped ipv6 address. |
| is_lock_improvement_enabled | bool | Boolean flag indicating whether lock improvement enabled. |
| is_mars | bool | Boolean flag indicating whether mars. |
| is_mfa | bool | Boolean flag indicating whether mfa. |
| is_mwc_system | bool | Boolean flag indicating whether mwc system. |
| is_mwc_user | bool | Boolean flag indicating whether mwc user. |
| is_normal_logout | bool | Boolean flag indicating whether normal logout. |
| is_nsp_claim_present | bool | Boolean flag indicating whether nsp claim present. |
| is_peer_activity_id_null | bool | Boolean flag indicating whether peer activity id null. |
| is_public_ipv6_rule | bool | Boolean flag indicating whether public ipv6 rule. |
| is_relogin | bool | Boolean flag indicating whether relogin. |
| is_replay_connection | bool | Boolean flag indicating whether replay connection. |
| is_skipped_by_nsp_check | bool | Boolean flag indicating whether skipped by nsp check. |
| is_skipped_by_private_endpoints | bool | Boolean flag indicating whether skipped by private endpoints. |
| is_slb_probe | bool | Boolean flag indicating whether slb probe. |
| is_success | bool | Boolean flag indicating whether success. |
| is_targeted_rule | bool | Boolean flag indicating whether targeted rule. |
| is_user_error | bool | Boolean flag indicating whether user error. |
| is_vnet_address | bool | Boolean flag indicating whether vnet address. |
| is_vnet_lookup | bool | Boolean flag indicating whether vnet lookup. |
| is_vnet_private_access_address | bool | Boolean flag indicating whether vnet private access address. |
| items_removed | long | Items removed. |
| kill_reason | string | Kill reason. |
| killed | long | Killed. |
| last_modified_time | datetime | Last modified time timestamp. |
| local_host | string | Local host. |
| local_port | long | Local port. |
| logical_database_guid | string | Logical database guid. |
| login7_bytes_remaining | long | Login7 size in bytes remaining. |
| login_correlation_hash | string | Login correlation hash. |
| login_flags | long | Login flags. |
| login_rec_len | long | Login rec len. |
| login_task_enqueued_ms | long | Login task enqueued ms in milliseconds. |
| login_time_ms | long | Login time ms in milliseconds. |
| login_trigger_and_resource_governor_processing_ms | long | Login trigger and resource governor processing ms in milliseconds. |
| logins_count | long | Number of logins. |
| logon_triggers_ms | long | Logon triggers ms in milliseconds. |
| logon_triggers_time_ms | long | Logon triggers time ms in milliseconds. |
| lookup_alias_cache_version | datetime | Lookup alias cache version. |
| lookup_alias_uri | string | Lookup alias uri. |
| lookup_error_code | string | Lookup error code. |
| lookup_error_state | long | State value for lookup error. |
| lookup_service_cache_version | datetime | Lookup service cache version. |
| lookup_state | string | State value for lookup. |
| message | string | Human-readable message text. |
| minTls | long | Min Tls. |
| minTls_comparison_skipped | bool | Boolean flag indicating whether min Tls comparison skipped. |
| netread_time_ms | long | Netread time ms in milliseconds. |
| network_reads_ms | long | Network reads ms in milliseconds. |
| network_writes_ms | long | Network writes ms in milliseconds. |
| netwrite_time_ms | long | Netwrite time ms in milliseconds. |
| nsp_validation_result | string | Nsp validation result. |
| nsp_validation_result_value | long | Nsp validation result value. |
| odbc_connection_id | string | Odbc connection identifier. |
| odbc_handle | long | Odbc handle. |
| odbc_state | string | State value for odbc. |
| open_running_count | long | Number of open running. |
| operation_id | string | Operation identifier for the workflow. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| os_error | long | OS error. |
| package | string | Package. |
| packet_count | long | Number of packet. |
| packets_read | long | Packets read. |
| packets_written | long | Packets written. |
| partition_id | string | Partition identifier. |
| peer_activity_id | string | Peer activity identifier. |
| peer_activity_seq | long | Peer activity seq. |
| peer_address | string | Peer address. |
| peer_port | long | Peer port. |
| pipe_name | string | Pipe name. |
| policy_based_external_authorization | string | Policy based external authorization. |
| post_exec_classifier_ms | long | Post exec classifier ms in milliseconds. |
| process_id | long | Process identifier. |
| prov_buffer_size | long | Prov buffer size. |
| prov_offset | long | Prov offset. |
| provider_name | string | Provider name. |
| provider_type | string | Type classification for provider. |
| proxy_dispacther_time_ms | long | Proxy dispacther time ms in milliseconds. |
| proxy_dispacther_wait_list_time_ms | long | Proxy dispacther wait list time ms in milliseconds. |
| proxy_open_time_ms | long | Proxy open time ms in milliseconds. |
| proxy_override | string | Proxy override. |
| read_scale_units | long | Read scale units. |
| record_id | long | Record identifier. |
| record_num | long | Record num. |
| redirection_map_id | string | Redirection map identifier. |
| remaining | long | Remaining. |
| remaining_dac_connections | long | Remaining dac connections. |
| remote_host | string | Remote host. |
| remote_port | long | Remote port. |
| resource_group_name | string | Resource group name. |
| resource_id | long | Resource identifier. |
| response | string | Response. |
| result | string | Result. |
| revised_instance_name | string | Revised instance name. |
| revised_instance_port | long | Revised instance port. |
| ring_name | string | Ring name. |
| root_ca_issuer | string | Root ca issuer. |
| send_byte_count | long | Number of send byte. |
| server_connection_state | long | State value for server connection. |
| server_name | string | Managed Instance server name. |
| servername_byte_count | long | Number of servername byte. |
| service_name | string | Service name. |
| sessionName | string | Session Name. |
| session_elapsed_time_ms | long | Session elapsed time ms in milliseconds. |
| session_id | long | Session identifier. |
| session_recover_ms | long | Session recover ms in milliseconds. |
| session_recovery_format_length | long | Session recovery format length. |
| session_recovery_is_enabled | bool | Boolean flag indicating whether session recovery enabled. |
| session_recovery_is_recovered | bool | Boolean flag indicating whether session recovery recovered. |
| set_result | long | Set result. |
| severity | long | Severity level associated with the event. |
| severityNumber | long | Severity Number. |
| severityText | string | Severity Text. |
| sni_conn_address | string | Sni conn address. |
| sni_conn_count | long | Number of sni conn. |
| sni_consumer_error | long | Sni consumer error. |
| sni_error | long | Sni error. |
| sni_provider | long | Sni provider. |
| sni_server_name | string | Sni server name. |
| sockdup_queue_size | long | Sockdup queue size. |
| source | string | Source. |
| source_uri | string | Source uri. |
| spid | long | Spid. |
| sql_client_dns_caching_status | long | Status value for SQL client dns caching. |
| sql_connection_id | string | SQL connection identifier. |
| sql_state | long | State value for SQL. |
| ssl_cipher | string | Ssl cipher. |
| ssl_cipher_suite | string | Ssl cipher suite. |
| ssl_dwhashlen | long | Ssl dwhashlen. |
| ssl_enqueue_ms | long | Ssl enqueue ms in milliseconds. |
| ssl_enqueue_time_ms | long | Ssl enqueue time ms in milliseconds. |
| ssl_hash | string | Ssl hash. |
| ssl_net_reads_ms | long | Ssl net reads ms in milliseconds. |
| ssl_net_writes_ms | long | Ssl net writes ms in milliseconds. |
| ssl_processing_ms | long | Ssl processing ms in milliseconds. |
| ssl_protocol | string | Ssl protocol. |
| ssl_read_time_ms | long | Ssl read time ms in milliseconds. |
| ssl_secure_call_time_ms | long | Ssl secure call time ms in milliseconds. |
| ssl_secure_calls_ms | long | Ssl secure calls ms in milliseconds. |
| ssl_time_ms | long | Ssl time ms in milliseconds. |
| ssl_write_time_ms | long | Ssl write time ms in milliseconds. |
| sspi_enqueue_ms | long | Sspi enqueue ms in milliseconds. |
| sspi_enqueue_time_ms | long | Sspi enqueue time ms in milliseconds. |
| sspi_net_reads_ms | long | Sspi net reads ms in milliseconds. |
| sspi_net_writes_ms | long | Sspi net writes ms in milliseconds. |
| sspi_processing_ms | long | Sspi processing ms in milliseconds. |
| sspi_read_time_ms | long | Sspi read time ms in milliseconds. |
| sspi_secure_call_time_ms | long | Sspi secure call time ms in milliseconds. |
| sspi_secure_calls_ms | long | Sspi secure calls ms in milliseconds. |
| sspi_time_ms | long | Sspi time ms in milliseconds. |
| sspi_write_time_ms | long | Sspi write time ms in milliseconds. |
| start_instance_port | long | Start instance port. |
| start_virtual_port | long | Start virtual port. |
| state | long | Current lifecycle or health state. |
| state_desc | string | State desc. |
| status | string | Current status reported by the component. |
| stepaction | string | Stepaction. |
| subnet_name | string | Subnet name. |
| tds_flags | string | Tds flags. |
| tds_input_buffer_bytes | long | Tds input buffer size in bytes. |
| tds_input_buffer_error | long | Tds input buffer error. |
| tds_output_buffer_error | long | Tds output buffer error. |
| tds_version | long | Tds version. |
| tdsproxycontainer_count | long | Number of tdsproxycontainer. |
| tdssession_count | long | Number of tdssession. |
| thumbprint | string | Thumbprint. |
| time_ms_deallocate | long | Time ms deallocate. |
| time_ms_detect | long | Time ms detect. |
| time_ms_remove | long | Time ms remove. |
| timeout_value | long | Timeout value. |
| timestamp_connectivity_ring_buffer_recorded | long | Timestamp connectivity ring buffer recorded. |
| total_login_time_ms | long | Total login time ms. |
| total_task_count | long | Number of total task. |
| total_tds_packet_size | long | Total tds packet size. |
| total_time_ms | long | Total time ms. |
| trace_level | long | Trace level. |
| type | string | Type. |
| use_db_database_firewall_rules_time_ms | long | Use database database firewall rules time ms in milliseconds. |
| used_login_thread_pool | bool | Boolean flag indicating whether used login thread pool. |
| user_agent | string | User agent. |
| validated_driver_name_and_version | string | Validated driver name and version. |
| vnet_dest_peer_address | string | Vnet dest peer address. |
| vnet_firewall_rules_count | long | Number of vnet firewall rules. |
| vnet_gre_key | long | Vnet gre key. |
| vnet_link_identifier | long | Vnet link identifier. |
| vnet_name | string | Vnet name. |
| vnet_peer_address | string | Vnet peer address. |
| vnet_region_id | long | Vnet region identifier. |
| vnet_rule_name | string | Vnet rule name. |
| vnet_subnet_id | long | Vnet subnet identifier. |
| web_socket_correlation_id | string | Web socket correlation identifier. |
| xodbc_authentication_time_ms | long | Xodbc authentication time ms in milliseconds. |
| xodbc_authentication_type | int | Type classification for xodbc authentication. |

## MonNetworkMonitoring — Network Monitoring

**Purpose**: Network Monitoring. Used to analyze connection establishment, routing, authentication, and client access failures. Referenced in MI template areas: networking.
**Category**: Networking

| Column | Type | Description |
|--------|------|-------------|
| collect_current_thread_id | long | Collect current thread identifier. |
| container_agent_host_port | long | Container agent host port. |
| dns_name | string | Dns name. |
| dns_server | string | Dns server. |
| dns_server_first | string | Dns server first. |
| dns_server_second | string | Dns server second. |
| event | string | Event name emitted by the component. |
| exception_message | string | Exception message. |
| exception_source | string | Exception source. |
| inner_exception | string | Inner exception. |
| ip_address | string | Ip address. |
| is_public | bool | Boolean flag indicating whether public. |
| log_level | string | Log level. |
| message | string | Human-readable message text. |
| move_instance_result | string | Move instance result. |
| new_node | string | New node. |
| old_node | string | Old node. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| port | long | Port. |
| process_id | long | Process identifier. |
| replica | string | Replica. |
| resolved_ip_address | string | Resolved ip address. |
| resolved_ip_address_first | string | Resolved ip address first. |
| resolved_ip_address_second | string | Resolved ip address second. |
| run_id | string | Run identifier. |
| sessionName | string | Session Name. |
| stack_trace | string | Stack trace. |
| total_time_ms | real | Total time ms. |

## MonRedirector — Redirector

**Purpose**: Redirector. Used to analyze connection establishment, routing, authentication, and client access failures. Referenced in MI template areas: networking, performance.
**Category**: Networking

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| MetricNamespace | string | Metric Namespace. |
| MonitoringAccount | string | Monitoring Account. |
| PartitionId | string | Partition Id. |
| alias_cache_entries | long | Alias cache entries. |
| alias_cache_pages_kb | long | Alias cache pages kb. |
| alias_cache_type | string | Type classification for alias cache. |
| alias_cache_vm_committed_kb | long | Alias cache vm committed kb. |
| application_name | string | Application name. |
| avg_duration_ticks | long | Average duration ticks. |
| backoff_duration_ms | long | Backoff duration ms in milliseconds. |
| backoff_status_message | string | Backoff status message. |
| cache_instance | string | Cache instance. |
| cache_type | string | Type classification for cache. |
| client_security_credentials | string | Client security credentials. |
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| connection_id | string | Connection identifier. |
| connection_string | string | Connection string. |
| data | string | Data. |
| dropped_notifications | long | Dropped notifications. |
| duration_ms | long | Duration in milliseconds. |
| endpoint | string | Endpoint. |
| entries | long | Entries. |
| entry | string | Entry. |
| entry_init_cost | long | Entry init cost. |
| error_code | string | Numeric error code for the failure or event. |
| error_number | long | SQL or platform error number. |
| event | string | Event name emitted by the component. |
| execution_time | long | Execution time timestamp. |
| expired_count | long | Number of expired. |
| fab_uri_cache | string | Fabric uri cache. |
| find_type | string | Type classification for find. |
| handler_id | long | Handler identifier. |
| health_state | string | State value for health. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| hresult | long | Hresult. |
| initialization_data | string | Initialization data. |
| instance | string | Instance. |
| instance_id | long | Instance identifier. |
| instance_port_end | long | Instance port end. |
| instance_port_start | long | Instance port start. |
| is_force_refreshed | bool | Boolean flag indicating whether force refreshed. |
| items | long | Items. |
| kind | string | Kind. |
| last_modified_time | datetime | Last modified time timestamp. |
| lookup_name | string | Lookup name. |
| max_concurrency | long | Maximum concurrency. |
| max_duration_ticks | long | Maximum duration ticks. |
| max_wait_time | long | Max wait time timestamp. |
| memory_clerk_name | string | Memory clerk name. |
| memory_clerk_type | string | Type classification for memory clerk. |
| memory_node_id | long | Memory node identifier. |
| message | string | Human-readable message text. |
| mgmtsvc_http_fail_max_time | long | Mgmtsvc http fail max time timestamp. |
| mgmtsvc_http_fail_total_time | long | Mgmtsvc http fail total time timestamp. |
| mgmtsvc_http_failed | long | Mgmtsvc http failed. |
| mgmtsvc_http_max_concurrent | long | Mgmtsvc http max concurrent. |
| mgmtsvc_http_opened | long | Mgmtsvc http opened. |
| mgmtsvc_http_succeeded | long | Mgmtsvc http succeeded. |
| mgmtsvc_http_success_max_time | long | Mgmtsvc http success max time timestamp. |
| mgmtsvc_http_success_total_time | long | Mgmtsvc http success total time timestamp. |
| min_tls_version | long | Minimum tls version. |
| new_version | string | New version. |
| notification_count | long | Number of notification. |
| odbc_connection_id | string | Odbc connection identifier. |
| odbc_handle | long | Odbc handle. |
| odbc_state | string | State value for odbc. |
| old_version | long | Old version. |
| open_mode | string | Open mode. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| originalUri | string | Original Uri. |
| original_error_code | string | Original error code. |
| package | string | Package. |
| pages_kb | long | Pages kb. |
| params_entry | string | Params entry. |
| partition_id | string | Partition identifier. |
| process_id | long | Process identifier. |
| property_name | string | Property name. |
| protection_level | string | Protection level. |
| queue_size | long | Queue size. |
| real_server_name | string | Real server name. |
| record_num | long | Record num. |
| remove_when_expired | bool | Boolean flag indicating whether remove when expired. |
| replica_id | long | Replica identifier. |
| resolve_duration_in_micro_seconds | long | Resolve duration in micro seconds. |
| resolve_result | string | Resolve result. |
| result | string | Result. |
| retry_count | long | Number of retry. |
| sequence_number | long | Sequence number. |
| server_security_credentials | string | Server security credentials. |
| service_address | string | Service address. |
| service_name | string | Service name. |
| service_type | string | Type classification for service. |
| sessionName | string | Session Name. |
| source_hash | long | Source hash. |
| source_id | string | Source identifier. |
| source_uri | string | Source uri. |
| source_version | long | Source version. |
| sql_connection_id | string | SQL connection identifier. |
| sql_state | string | State value for SQL. |
| stale_data | bool | Boolean flag indicating whether stale data. |
| state | long | Current lifecycle or health state. |
| store_location | string | Store location. |
| text | string | Text. |
| time_to_live_in_seconds | long | Time to live in seconds. |
| trace_level | long | Trace level. |
| uri_cache_entries | long | Uri cache entries. |
| uri_cache_pages_kb | long | Uri cache pages kb. |
| uri_cache_vm_committed_kb | long | Uri cache vm committed kb. |
| use_real_server_aliases | bool | Boolean flag indicating whether use real server aliases. |
| version | long | Version. |
| virtual_port_start | long | Virtual port start. |
| vm_committed_kb | long | Vm committed kb. |
| wait_completed | long | Wait completed. |
| wait_group | string | Wait group. |
| wait_name | string | Wait name. |
| wait_reason | string | Wait reason. |
| wait_requests | long | Wait requests. |
| wait_sigtime | long | Wait sigtime. |
| wait_time | long | Wait time timestamp. |
| wait_type | long | Wait type name. |

## MonSqlFrontend — SQL Frontend

**Purpose**: SQL Frontend. Used to analyze connection establishment, routing, authentication, and client access failures. Referenced in MI template areas: performance. Often used to explain wait or latency patterns.
**Category**: Networking

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppName_frontend_memory_usage | string | App Name frontend memory usage. |
| AppTypeName_Ex | string | App Type Name Ex. |
| AppTypeName_frontend_memory_usage | string | App Type Name frontend memory usage. |
| PartitionId | string | Partition Id. |
| avg_file_path_length | long | Average file path length. |
| batch_id | string | Batch identifier. |
| batch_size | long | Batch size. |
| batch_sql_hash | string | Batch SQL hash. |
| binding_state | string | State value for binding. |
| cancellation_latency | long | Cancellation latency. |
| code_package_version | string | Code package version. |
| database_id | long | Database identifier. |
| directory_listing_error_code | long | Directory listing error code. |
| duration | long | Duration. |
| eliminate_partitions | bool | Boolean flag indicating whether eliminate partitions. |
| empty_files | long | Empty files. |
| equality_replacement_ordinals | string | Equality replacement ordinals. |
| event | string | Event name emitted by the component. |
| external_database_state | long | State value for external database. |
| failure_reason | string | Failure reason. |
| file_path_hash | string | File path hash. |
| flags | long | Flags. |
| format_type | string | Type classification for format. |
| frontend_component | string | Frontend component. |
| function_name | string | Function name. |
| group_number | long | Group number. |
| has_external_database_target | bool | Boolean flag indicating whether has external database target. |
| hns_detection_duration_ms | long | Hns detection duration ms in milliseconds. |
| hns_detection_error_number | long | Hns detection error number. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| is_cardinality_compilation | bool | Boolean flag indicating whether cardinality compilation. |
| is_cardinality_query | bool | Boolean flag indicating whether cardinality query. |
| is_cetas | bool | Boolean flag indicating whether cetas. |
| is_external_table | bool | Boolean flag indicating whether external table. |
| is_external_table_stats | bool | Boolean flag indicating whether external table stats. |
| is_hns_enabled | bool | Boolean flag indicating whether hns enabled. |
| is_openrowset | bool | Boolean flag indicating whether openrowset. |
| is_openrowset_stats | bool | Boolean flag indicating whether openrowset stats. |
| is_pattern_const | bool | Boolean flag indicating whether pattern const. |
| is_text_const | bool | Boolean flag indicating whether text const. |
| is_text_lob | bool | Boolean flag indicating whether text lob. |
| is_user_query_in_recompile | bool | Boolean flag indicating whether user query in recompile. |
| largest_file_size_bytes | long | Largest file size size in bytes. |
| line_number | long | Line number. |
| list_dir_calls | long | List dir calls. |
| list_dir_items_processed | long | List dir items processed. |
| listing_policy | string | Listing policy. |
| listing_requests_duration_ms | long | Listing requests duration ms in milliseconds. |
| logical_database_guid | string | Logical database guid. |
| logical_database_name | string | Logical database name. |
| masked_pattern | string | Masked pattern. |
| matches_found | long | Matches found. |
| matching_duration_ms | long | Matching duration ms in milliseconds. |
| max_file_path_length | long | Maximum file path length. |
| memory_allocated_kb | long | Memory allocated kb. |
| number_of_recompiles_triggered | long | Number of recompiles triggered. |
| obfuscated_file_path | string | Obfuscated file path. |
| object_id | long | Object identifier. |
| occurrence | long | Occurrence. |
| offset | long | Offset. |
| offset_end | long | Offset end. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| pattern_length | long | Pattern length. |
| polybase_enabled | long | Polybase enabled. |
| prefix_length | long | Prefix length. |
| process_metadata_duration_ms | long | Process metadata duration ms in milliseconds. |
| query_hash | string | Query hash. |
| query_plan_hash | string | Query plan hash. |
| query_type | string | Type classification for query. |
| recompile_time | long | Recompile time timestamp. |
| recompile_time_threshold | long | Recompile time threshold. |
| resource_group_id | long | Resource group identifier. |
| resource_pool_id | long | Resource pool identifier. |
| return_option | bool | Boolean flag indicating whether return option. |
| search_index | long | Search index. |
| sessionName | string | Session Name. |
| smallest_file_size_bytes | long | Smallest file size size in bytes. |
| sql_error_number | long | SQL error number. |
| sql_error_severity | long | SQL error severity. |
| sql_error_state | long | State value for SQL error. |
| statement_number | long | Statement number. |
| statement_sql_hash | string | Statement SQL hash. |
| status | string | Current status reported by the component. |
| string_replacement_length | long | String replacement length. |
| suffix_length | long | Suffix length. |
| threshold_number_of_recompiles_triggered | long | Threshold number of recompiles triggered. |
| timeout_seconds | long | Timeout seconds. |
| total_conjunct_count | long | Number of total conjunct. |
| total_list_directories_duration_ms | long | Total list directories duration ms. |
| total_size_bytes | long | Total size size in bytes. |
| union_count | long | Number of union. |
| vector_function_name | string | Vector function name. |
| xstore_file_path_type | string | Type classification for xstore file path. |

## MonUcsConnections — UCS Connections

**Purpose**: UCS Connections. Used to analyze connection establishment, routing, authentication, and client access failures. Referenced in MI template areas: availability.
**Category**: Networking

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| Level | long | Level. |
| Name | string | Object or resource name. |
| OneBoxClusterId | string | One Box Cluster Id. |
| PartitionId | string | Partition Id. |
| Pid | long | Pid. |
| Tid | long | Tid. |
| Timestamp | string | timestamp. |
| _name | string | Name. |
| acceptor_authentication_protocol | string | Acceptor authentication protocol. |
| acceptor_encryption_algorithm | string | Acceptor encryption algorithm. |
| acceptor_signature_algorithm | string | Acceptor signature algorithm. |
| address | string | Address. |
| attach_activity_id | string | Attach activity identifier. |
| attach_activity_id_xfer | string | Attach activity id xfer. |
| auth_error_op | long | Auth error op. |
| auth_error_state | long | State value for auth error. |
| availability_group_id | string | Availability group identifier. |
| body | string | Body. |
| change_destination_status | bool | Boolean flag indicating whether change destination status. |
| circuit_id | string | Circuit identifier. |
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| connect_string | string | Connect string. |
| connection_count | long | Number of connection. |
| connection_encryption_mode | string | Connection encryption mode. |
| connection_id | string | Connection identifier. |
| connection_index | long | Connection index. |
| curr_invoked_tasks | long | Curr invoked tasks. |
| curr_scheduled_tasks | long | Curr scheduled tasks. |
| currently_connecting | bool | Boolean flag indicating whether currently connecting. |
| destination_id | long | Destination identifier. |
| destination_status_flag | string | Destination status flag. |
| dispatch_task_inrunning_microsecond | long | Dispatch task inrunning microsecond. |
| dispatch_task_inscheduled_microsecond | long | Dispatch task inscheduled microsecond. |
| duration | long | Duration. |
| encrypted_offset | long | Encrypted offset. |
| endpoint_type | string | Type classification for endpoint. |
| error | long | Error text captured for the event or operation. |
| error_code | long | Numeric error code for the failure or event. |
| error_message | string | Error message. |
| error_number | long | SQL or platform error number. |
| event | string | Event name emitted by the component. |
| event_ucs_transmitter_destination_event | string | Event UCS transmitter destination event. |
| flow_control_event | string | Flow control event. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| initiate_redirection | bool | Boolean flag indicating whether initiate redirection. |
| initiator_authentication_protocol | string | Initiator authentication protocol. |
| initiator_encryption_algorithm | string | Initiator encryption algorithm. |
| initiator_signature_algorithm | string | Initiator signature algorithm. |
| ip_port_name | string | Ip port name. |
| is_completed | bool | Boolean flag indicating whether completed. |
| is_initiator | bool | Boolean flag indicating whether initiator. |
| local_availability_replica_id | string | Local availability replica identifier. |
| local_endpoint_type | string | Type classification for local endpoint. |
| local_key | long | Local key. |
| local_max_protocol_version | string | Local max protocol version. |
| local_min_protocol_version | string | Local min protocol version. |
| max_invoked_tasks | long | Maximum invoked tasks. |
| max_scheduled_tasks | long | Maximum scheduled tasks. |
| message_class | long | Message class. |
| message_corruption | string | Message corruption. |
| message_protocol | long | Message protocol. |
| message_size | long | Message size. |
| min_invoked_tasks | long | Minimum invoked tasks. |
| min_scheduled_tasks | long | Minimum scheduled tasks. |
| negotiated_encryption_algorithm | string | Negotiated encryption algorithm. |
| negotiated_first_authentication_protocol | string | Negotiated first authentication protocol. |
| negotiated_protocol_version | string | Negotiated protocol version. |
| negotiated_second_authentication_protocol | string | Negotiated second authentication protocol. |
| negotiated_signature_algorithm | string | Negotiated signature algorithm. |
| new_status_version | long | New status version. |
| new_stream_status | string | Status value for new stream. |
| num_dbm_task_handlers | long | Num dbm task handlers. |
| num_messages | long | Num messages. |
| num_prioritized_connection_task_handlers | long | Num prioritized connection task handlers. |
| num_sessions | long | Num sessions. |
| num_task_handlers | long | Num task handlers. |
| obj_address | string | Obj address. |
| operation | string | Operation. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| other_connections_flow_control_or_connecting | bool | Boolean flag indicating whether other connections flow control or connecting. |
| other_connections_ready | bool | Boolean flag indicating whether other connections ready. |
| package | string | Package. |
| pending_recv_messages | long | Pending recv messages. |
| pending_send_boxcars | long | Pending send boxcars. |
| period_ms | long | Period ms in milliseconds. |
| phase | string | Phase. |
| process_id | long | Process identifier. |
| reconnect_all | bool | Boolean flag indicating whether reconnect all. |
| recv_bytes_actual | long | Recv size in bytes actual. |
| recv_bytes_posted | long | Recv size in bytes posted. |
| recv_ios | long | Recv ios. |
| recv_msg_bytes_raw | long | Recv msg size in bytes raw. |
| recv_msgs | long | Recv msgs. |
| recv_task_inrunning_microsecond | long | Recv task inrunning microsecond. |
| recv_task_inscheduled_microsecond | long | Recv task inscheduled microsecond. |
| recv_task_invoked | long | Recv task invoked. |
| redirected_to_connection_id | string | Redirected to connection identifier. |
| ref_count | long | Number of ref. |
| remote_endpoint_type | string | Type classification for remote endpoint. |
| remote_max_protocol_version | string | Remote max protocol version. |
| remote_min_protocol_version | string | Remote min protocol version. |
| renegotiation_completion_count | long | Number of renegotiation completion. |
| result | bool | Boolean flag indicating whether result. |
| send_failure_block_period | long | Send failure block period. |
| send_failure_threshold | long | Send failure threshold. |
| send_task_inrunning_microsecond | long | Send task inrunning microsecond. |
| send_task_inscheduled_microsecond | long | Send task inscheduled microsecond. |
| sent_bytes | long | Sent size in bytes. |
| sent_ios | long | Sent ios. |
| sent_msg_bytes_raw | long | Sent msg size in bytes raw. |
| sent_msgs | long | Sent msgs. |
| service_address | string | Service address. |
| service_id | long | Service identifier. |
| service_instance | string | Service instance. |
| service_name | string | Service name. |
| sessionName | string | Session Name. |
| session_address | string | Session address. |
| session_id | string | Session identifier. |
| session_initiator | bool | Boolean flag indicating whether session initiator. |
| setup_event | string | Setup event. |
| severityNumber | long | Severity Number. |
| severityText | string | Severity Text. |
| ssl_cipher | string | Ssl cipher. |
| ssl_cipher_suite | string | Ssl cipher suite. |
| ssl_hash | string | Ssl hash. |
| ssl_protocol | long | Ssl protocol. |
| stage | string | Stage. |
| state | long | Current lifecycle or health state. |
| state_current | string | State current. |
| state_new | string | State new. |
| state_old | string | State old. |
| status_version | long | Status version. |
| stepaction | string | Stepaction. |
| stream_status | string | Status value for stream. |
| stream_update | string | Stream update. |
| system_thread_id | long | System thread identifier. |
| target_address | string | Target address. |
| target_availability_replica_id | string | Target availability replica identifier. |
| target_connection_count | long | Number of target connection. |
| task_handler_partition_avg | real | Task handler partition avg. |
| task_handler_partition_max | long | Task handler partition max. |
| task_handler_partition_min | long | Task handler partition min. |
| task_handler_partition_var | real | Task handler partition var. |
| task_mgr_options | long | Task mgr options. |
| task_partition_avg | real | Task partition avg. |
| task_partition_max | long | Task partition max. |
| task_partition_min | long | Task partition min. |
| task_partition_var | real | Task partition var. |
| total_invoked_tasks | long | Total invoked tasks. |
| total_kickedoff_taskhandlers | long | Total kickedoff taskhandlers. |
| ucs_connection_id | string | UCS connection identifier. |
| ucs_handshake_state | string | State value for UCS handshake. |
| use_aes_256 | bool | Boolean flag indicating whether use aes 256. |

## MonUpsertTenantRingRequests — Upsert Tenant Ring Requests

**Purpose**: Upsert Tenant Ring Requests. Used to analyze connection establishment, routing, authentication, and client access failures. Referenced in MI template areas: availability, networking. Often used to correlate SQL behavior with Service Fabric activity.
**Category**: Networking

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| abandon_ring_resize_da_instance_id | string | Abandon ring resize da instance identifier. |
| build_fabric_cluster_da_instance_id | string | Build fabric cluster da instance identifier. |
| buildout_cluster_configuration | string | Buildout cluster configuration. |
| buildout_ring_type | string | Type classification for buildout ring. |
| code_package_version | string | Code package version. |
| concurrency_token | long | Concurrency token. |
| create_fabric_cluster_da_instance_id | string | Create fabric cluster da instance identifier. |
| create_time | datetime | Creation timestamp. |
| da_application_type_version | string | Da application type version. |
| dns_prefix | string | Dns prefix. |
| end_utc_date | datetime | End utc date. |
| fabric_cluster_name | string | Fabric cluster name. |
| finalize_fabric_cluster_da_instance_id | string | Finalize fabric cluster da instance identifier. |
| fsm_context_instance_name | string | Fsm context instance name. |
| fsm_extension_data | string | Fsm extension data. |
| fsm_instance_id | string | Fsm instance identifier. |
| fsm_timer_event_version | long | Fsm timer event version. |
| fsm_version | long | Fsm version. |
| hardware_generation | string | Hardware generation. |
| infra_subnet_manager_id | string | Infra subnet manager identifier. |
| initialize_fabric_cluster_da_instance_id | string | Initialize fabric cluster da instance identifier. |
| is_cmw_provisioning | long | Boolean flag indicating whether cmw provisioning. |
| is_error_state | long | Boolean flag indicating whether error state. |
| is_manual_create_initialize_finalize | long | Boolean flag indicating whether manual create initialize finalize. |
| is_manual_provisioning | long | Boolean flag indicating whether manual provisioning. |
| is_reserved | long | Boolean flag indicating whether reserved. |
| is_resizable | long | Boolean flag indicating whether resizable. |
| is_stable_state | long | Boolean flag indicating whether stable state. |
| is_swift | long | Boolean flag indicating whether swift. |
| last_exception | string | Last exception. |
| last_state_change_time | datetime | Last state change time timestamp. |
| last_update_time | datetime | Last update time timestamp. |
| next_successor | long | Next successor. |
| pinned_subnet_resource_id | string | Pinned subnet resource identifier. |
| remove_fabric_cluster_da_instance_id | string | Remove fabric cluster da instance identifier. |
| request_id | string | Request identifier used to correlate the operation. |
| resize_fabric_cluster_da_instance_id | string | Resize fabric cluster da instance identifier. |
| ring_buildout_id | string | Ring buildout identifier. |
| start_utc_date | datetime | Start utc date. |
| state | string | Current lifecycle or health state. |
| storage_subscription_id | string | Storage subscription identifier. |
| subnet_address_range | string | Subnet address range. |
| subnet_address_range_ipv6 | string | Subnet address range ipv6. |
| subnet_name | string | Subnet name. |
| subnet_resource_id | string | Subnet resource identifier. |
| supports_multi_db_roles | long | Supports multi database roles. |
| supports_small_vms | long | Supports small vms. |
| target_number_of_nodes_per_role | string | Target number of nodes per role. |
| tenant_ring_name | string | Tenant ring name. |
| unprotect_fabric_cluster_da_instance_id | string | Unprotect fabric cluster da instance identifier. |
| update_cluster_infrastructure_da_instance_id | string | Update cluster infrastructure da instance identifier. |
| update_fabric_cluster_infrastructure_overrides_da_instance_id | string | Update fabric cluster infrastructure overrides da instance identifier. |
| vnet_resource_guid | string | Vnet resource guid. |
| vnet_resource_id | string | Vnet resource identifier. |

## MonXdbhost — Xdbhost

**Purpose**: Xdbhost. Used to analyze connection establishment, routing, authentication, and client access failures. Referenced in MI template areas: availability, networking.
**Category**: Networking

| Column | Type | Description |
|--------|------|-------------|
| Level | long | Level. |
| Name | string | Object or resource name. |
| OneBoxClusterId | string | One Box Cluster Id. |
| Pid | long | Pid. |
| Tid | long | Tid. |
| Timestamp | string | timestamp. |
| _name | string | Name. |
| action | string | Action. |
| application_name | string | Application name. |
| body | string | Body. |
| certificate_hash | string | Certificate hash. |
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| connection_id | string | Connection identifier. |
| error | long | Error text captured for the event or operation. |
| event | string | Event name emitted by the component. |
| health_state | string | State value for health. |
| initialization_data | string | Initialization data. |
| instance | string | Instance. |
| instance_id | long | Instance identifier. |
| instance_name | string | Instance name. |
| kind | string | Kind. |
| open_mode | string | Open mode. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| partition_id | string | Partition identifier. |
| process_handle | string | Process handle. |
| process_id | long | Process identifier. |
| property_name | string | Property name. |
| remove_when_expired | bool | Boolean flag indicating whether remove when expired. |
| replica_id | long | Replica identifier. |
| result | string | Result. |
| sequence_number | long | Sequence number. |
| service_address | string | Service address. |
| service_name | string | Service name. |
| service_type | string | Type classification for service. |
| sessionName | string | Session Name. |
| severityNumber | long | Severity Number. |
| severityText | string | Severity Text. |
| source_id | string | Source identifier. |
| sqlserver_name | string | Sqlserver name. |
| state | string | Current lifecycle or health state. |
| text | string | Text. |
| time_to_live_in_seconds | long | Time to live in seconds. |

# 6. Query Performance

## MonAttentions — Attentions

**Purpose**: Attentions. Used to investigate slow queries, waits, blocking, deadlocks, and Query Store behavior. Referenced in MI template areas: performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| client_pid | long | Client pid. |
| code_package_version | string | Code package version. |
| database_name | string | Database name. |
| duration | long | Duration. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| request_id | long | Request identifier used to correlate the operation. |
| session_id | long | Session identifier. |

## MonBlockedProcessReportFiltered — Blocked Process Report Filtered

**Purpose**: Blocked Process Report Filtered. Used to investigate slow queries, waits, blocking, deadlocks, and Query Store behavior. Referenced in MI template areas: performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| ResourcePoolName | string | Resource Pool Name. |
| blocked_process_filtered | string | Blocked process filtered. |
| code_package_version | string | Code package version. |
| context_info | string | Context info. |
| database_id | long | Database identifier. |
| database_name | string | Database name. |
| duration | long | Duration. |
| event | string | Event name emitted by the component. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| index_id | long | Index identifier. |
| instance_rg_size | string | Instance resource governor size. |
| lock_mode | string | Lock mode. |
| logical_database_name | string | Logical database name. |
| object_id | long | Object identifier. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| resource_owner_type | string | Type classification for resource owner. |
| sessionName | string | Session Name. |
| session_id | long | Session identifier. |
| transaction_id | long | Transaction identifier. |

## MonDeadlockReportsFiltered — Deadlock Reports Filtered

**Purpose**: Deadlock Reports Filtered. Used to investigate slow queries, waits, blocking, deadlocks, and Query Store behavior. Referenced in MI template areas: performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| ResourcePoolName | string | Resource Pool Name. |
| blocked_callstack | string | Blocked callstack. |
| blocked_callstack_rva | string | Blocked callstack rva. |
| blocked_count | long | Number of blocked. |
| code_package_version | string | Code package version. |
| current_blocked | string | Current blocked. |
| database_name | string | Database name. |
| event | string | Event name emitted by the component. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| next_blocked | string | Next blocked. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| sessionName | string | Session Name. |
| timestamp_id | long | Timestamp identifier. |
| xml_report_filtered | string | Xml report filtered. |

## MonDmExecCachedPlansSummary — DM Exec Cached Plans Summary

**Purpose**: DM Exec Cached Plans Summary. Used to investigate slow queries, waits, blocking, deadlocks, and Query Store behavior. Referenced in MI template areas: performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| cacheobjtype | string | Cacheobjtype. |
| code_package_version | string | Code package version. |
| end_utc_date | datetime | End utc date. |
| objtype | string | Objtype. |
| pool_id | long | Pool identifier. |
| refcounts_avg | long | Refcounts avg. |
| refcounts_max | long | Refcounts max. |
| refcounts_sum | long | Refcounts sum. |
| size_in_megabytes_avg | real | Size in megabytes avg. |
| size_in_megabytes_max | real | Size in megabytes max. |
| size_in_megabytes_min | real | Size in megabytes min. |
| size_in_megabytes_sum | real | Size in megabytes sum. |
| start_utc_date | datetime | Start utc date. |
| total | long | Total. |
| usecounts_avg | long | Usecounts avg. |
| usecounts_max | long | Usecounts max. |
| usecounts_sum | long | Usecounts sum. |

## MonQPTelemetry — QPTelemetry

**Purpose**: QPTelemetry. Used to investigate slow queries, waits, blocking, deadlocks, and Query Store behavior. Referenced in MI template areas: performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| collect_system_time | datetime | Collect system time timestamp. |
| compile_plan_guid | string | Compile plan guid. |
| database_id | long | Database identifier. |
| distributed_execution_id | string | Distributed execution identifier. |
| distributed_query_hash | string | Distributed query hash. |
| distributed_query_operator_id | string | Distributed query operator identifier. |
| distributed_request_id | string | Distributed request identifier. |
| distributed_scheduler_id | string | Distributed scheduler identifier. |
| distributed_statement_id | string | Distributed statement identifier. |
| distributed_step_index | string | Distributed step index. |
| distributed_submission_id | string | Distributed submission identifier. |
| distributed_task_group_id | string | Distributed task group identifier. |
| event | string | Event name emitted by the component. |
| execution_plan_guid | string | Execution plan guid. |
| logical_database_guid | string | Logical database guid. |
| logical_database_name | string | Logical database name. |
| object_id | long | Object identifier. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| physical_database_guid | string | Physical database guid. |
| plan_handle | string | Plan handle. |
| query_hash | long | Query hash. |
| query_hash_signed | long | Query hash signed. |
| query_plan_hash | long | Query plan hash. |
| query_plan_hash_signed | long | Query plan hash signed. |
| sessionName | string | Session Name. |
| sql_handle | string | SQL handle. |
| telemetry_package_json | string | Telemetry package json. |
| telemetry_package_name | string | Telemetry package name. |
| telemetry_package_version | long | Telemetry package version. |

## MonQueryProcessing — Query Processing

**Purpose**: Query Processing. Used to investigate slow queries, waits, blocking, deadlocks, and Query Store behavior. Referenced in MI template areas: performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| abort_state | long | State value for abort. |
| active_compiles | long | Active compiles. |
| actual_card | real | Actual card. |
| actual_execution_mode | string | Actual execution mode. |
| actual_rows | long | Actual rows. |
| adjustment_count | long | Number of adjustment. |
| aggregation_count | long | Number of aggregation. |
| alternate_card | real | Alternate card. |
| analysis_count | long | Number of analysis. |
| analytical_mode_forced_by_hint_or_db_scoped_config | long | Analytical mode forced by hint or database scoped config. |
| antipattern_type | string | Type classification for antipattern. |
| async | bool | Boolean flag indicating whether async. |
| available_memory_kb | long | Available memory kb. |
| avg_adjusted_elapsed_time_ms | long | Average adjusted elapsed time ms. |
| avg_cpu_time_ms | long | Average CPU time ms. |
| avg_delete_find_neighbors_phase_ms | long | Average delete find neighbors phase ms. |
| avg_delete_total_ms | long | Average delete total ms. |
| avg_delete_update_edges_phase_ms | long | Average delete update edges phase ms. |
| avg_insert_search_phase_ms | long | Average insert search phase ms. |
| avg_insert_total_ms | long | Average insert total ms. |
| avg_insert_update_phase_ms | long | Average insert update phase ms. |
| avg_operation_duration_ms | long | Average operation duration ms. |
| avg_parallelism_wait_time_ms | long | Average parallelism wait time ms. |
| baseline_avg_adjusted_elapsed_time_ms | long | Baseline avg adjusted elapsed time ms in milliseconds. |
| baseline_avg_cpu_time_ms | long | Baseline avg CPU time ms in milliseconds. |
| baseline_avg_parallelism_wait_time_ms | long | Baseline avg parallelism wait time ms in milliseconds. |
| baseline_std_dev_adjusted_elapsed_time_ms | long | Baseline std dev adjusted elapsed time ms in milliseconds. |
| baseline_std_dev_cpu_time_ms | long | Baseline std dev CPU time ms in milliseconds. |
| baseline_std_dev_parallelism_wait_time_ms | long | Baseline std dev parallelism wait time ms in milliseconds. |
| batch_count | long | Number of batch. |
| batch_id | string | Batch identifier. |
| batchmode_func_groups | string | Batchmode func groups. |
| big_gateway_active_acquires | long | Big gateway active acquires. |
| big_gateway_count_waiters | long | Big gateway count waiters. |
| big_gateway_threshold | long | Big gateway threshold. |
| big_gateway_throughput | long | Big gateway throughput. |
| blocked_reason | string | Blocked reason. |
| blocking_lock_mode | string | Blocking lock mode. |
| blocking_plan_handle | string | Blocking plan handle. |
| blocking_query_hash | long | Blocking query hash. |
| blocking_query_plan_hash | long | Blocking query plan hash. |
| blocking_session_id | long | Blocking session identifier. |
| blocking_sql_handle | string | Blocking SQL handle. |
| bp_workfile_memory_kb | long | Bp workfile memory kb. |
| cardinality_all_conditions | real | Cardinality all conditions. |
| ce_calculator | long | Ce calculator. |
| check_queue_size | long | Check queue size. |
| code_package_version | string | Code package version. |
| collect_system_time | datetime | Collect system time timestamp. |
| column_collation | long | Column collation. |
| column_id | long | Column identifier. |
| column_name | string | Column name. |
| compat_level_satisfied | bool | Boolean flag indicating whether compat level satisfied. |
| compilation_stage | long | Compilation stage. |
| compile_cpu | long | Compile CPU. |
| compile_duration | long | Compile duration. |
| compile_plan_guid | string | Compile plan guid. |
| compile_time | bool | Compile time timestamp. |
| compilecpu_time_ms | long | Compilecpu time ms in milliseconds. |
| corrective_action | long | Corrective action. |
| count | long | Number of count. |
| count_predicates_added | long | Number of count predicates added. |
| cte_level | long | Cte level. |
| cte_name | string | Cte name. |
| cte_status | string | Status value for cte. |
| curr_leading_col_sort_type | int | Type classification for curr leading col sort. |
| current_execution_count | long | Number of current execution. |
| current_interval | long | Current interval. |
| current_interval_execution_count | long | Number of current interval execution. |
| database_id | long | Database identifier. |
| database_name | string | Database name. |
| db_id | long | Database identifier. |
| default_dop | long | Default dop. |
| dimensions | long | Dimensions. |
| distributed_execution_id | string | Distributed execution identifier. |
| distributed_query_hash | string | Distributed query hash. |
| distributed_query_operator_id | string | Distributed query operator identifier. |
| distributed_request_id | string | Distributed request identifier. |
| distributed_scheduler_id | string | Distributed scheduler identifier. |
| distributed_statement_id | string | Distributed statement identifier. |
| distributed_step_index | string | Distributed step index. |
| distributed_submission_id | string | Distributed submission identifier. |
| distributed_task_group_id | string | Distributed task group identifier. |
| dop | long | Dop. |
| duration | long | Duration. |
| duration_of_wlp_minutes | long | Duration of wlp minutes. |
| embedding_column_dimensions | long | Embedding column dimensions. |
| equal_to_prev_str | bool | Boolean flag indicating whether equal to prev str. |
| error_code | long | Numeric error code for the failure or event. |
| error_message | string | Error message. |
| error_number | long | SQL or platform error number. |
| error_severity | long | Error severity. |
| error_state | long | State value for error. |
| estimated_build_side_row_count | long | Number of estimated build side row. |
| estimated_card | real | Estimated card. |
| estimated_num_of_rows_read | real | Estimated num of rows read. |
| estimated_probe_side_row_count | long | Number of estimated probe side row. |
| estimated_rows | long | Estimated rows. |
| event | string | Event name emitted by the component. |
| event_type | long | Type classification for event. |
| execution_plan_guid | string | Execution plan guid. |
| explanation | string | Explanation. |
| expression_fingerprint | string | Expression fingerprint. |
| failed_concurrent_update_count | long | Number of failed concurrent update. |
| failed_task_count | long | Number of failed task. |
| feature_enabled | bool | Boolean flag indicating whether feature enabled. |
| feedback | string | Feedback. |
| feedback_dop | long | Feedback dop. |
| feedback_hint | string | Feedback hint. |
| feedback_json | string | Feedback json. |
| feedback_validation_cpu_time | long | Feedback validation CPU time timestamp. |
| feedback_validation_plan_hash | long | Feedback validation plan hash. |
| filter_strategy | long | Filter strategy. |
| final_memory_grant_kb | long | Final memory grant kb. |
| final_required_memory_kb | long | Final required memory kb. |
| fingerprint | string | Fingerprint. |
| forced_grant_count | long | Number of forced grant. |
| forced_plan_id | long | Forced plan identifier. |
| full_optimization | long | Full optimization. |
| fullopt_time_ms | long | Fullopt time ms in milliseconds. |
| gateway_delta | long | Gateway delta. |
| gateway_name | string | Gateway name. |
| gateway_number | long | Gateway number. |
| gateway_threshold | long | Gateway threshold. |
| global_hash_table_bytes | long | Global hash table size in bytes. |
| granted_memory_kb | long | Granted memory kb. |
| grantee_count | long | Number of grantee. |
| group_by_column_data_type | string | Type classification for group by column data. |
| group_by_column_id | long | Group by column identifier. |
| group_by_count | long | Number of group by. |
| group_id | long | Group identifier. |
| guess_type | long | Type classification for guess. |
| guid | string | Guid. |
| has_expensive_compare_type | bool | Boolean flag indicating whether has expensive compare type. |
| hash_data_bytes | long | Hash data size in bytes. |
| history_current_execution_count | long | Number of history current execution. |
| history_update_count | long | Number of history update. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| ideal_additional_memory_after_kb | long | Ideal additional memory after kb. |
| ideal_additional_memory_before_kb | long | Ideal additional memory before kb. |
| ideal_memory_grant_kb | long | Ideal memory grant kb. |
| ideal_memory_kb | long | Ideal memory kb. |
| incremental | bool | Boolean flag indicating whether incremental. |
| index_id | long | Index identifier. |
| index_name | string | Index name. |
| interesting_predicate_count | long | Number of interesting predicate. |
| interesting_predicate_details | string | Interesting predicate details. |
| intrinsic_metric_name | string | Intrinsic metric name. |
| intrinsic_name | string | Intrinsic name. |
| is_candidate_for_simple_param | bool | Boolean flag indicating whether candidate for simple param. |
| is_columnstore | bool | Boolean flag indicating whether columnstore. |
| is_columnstore_bulk_insert | bool | Boolean flag indicating whether columnstore bulk insert. |
| is_desc_index | bool | Boolean flag indicating whether desc index. |
| is_filtered | bool | Boolean flag indicating whether filtered. |
| is_group_by_column_nullable | bool | Boolean flag indicating whether group by column nullable. |
| is_openrowset | bool | Boolean flag indicating whether openrowset. |
| is_optimization_applied | bool | Boolean flag indicating whether optimization applied. |
| is_persisted_feedback_used | bool | Boolean flag indicating whether persisted feedback used. |
| is_plan_cache_store | bool | Boolean flag indicating whether plan cache store. |
| is_query_variant | bool | Boolean flag indicating whether query variant. |
| is_runtime_reassessment | bool | Boolean flag indicating whether runtime reassessment. |
| job_id | long | Job identifier. |
| job_type | string | Type classification for job. |
| join_column_count | long | Number of join column. |
| join_strategy | long | Join strategy. |
| k_value | long | K value. |
| l_value | long | L value. |
| last_error | long | Last error. |
| last_highest_inserted_id | long | Last highest inserted identifier. |
| last_iteration_begin_id | long | Last iteration begin identifier. |
| last_iteration_end_id | long | Last iteration end identifier. |
| last_pending_deletes | long | Last pending deletes. |
| last_pending_inserts | long | Last pending inserts. |
| leading_column_collation | string | Leading column collation. |
| leading_column_length | long | Leading column length. |
| leading_column_precision | long | Leading column precision. |
| leading_column_scale | long | Leading column scale. |
| leading_column_type | string | Type classification for leading column. |
| lock_mode | string | Lock mode. |
| lock_wait_time_ms | long | Lock wait time ms in milliseconds. |
| logical_database_guid | string | Logical database guid. |
| logical_database_name | string | Logical database name. |
| m_value | long | M value. |
| max_additional_memory_kb_from_plan | long | Maximum additional memory kb from plan. |
| max_allowed_query_memory_kb | long | Maximum allowed query memory kb. |
| max_check_queue_size | long | Maximum check queue size. |
| max_compiles | long | Maximum compiles. |
| max_delete_find_neighbors_phase_ms | long | Maximum delete find neighbors phase ms. |
| max_delete_total_ms | long | Maximum delete total ms. |
| max_delete_update_edges_phase_ms | long | Maximum delete update edges phase ms. |
| max_dop | long | Maximum dop. |
| max_insert_search_phase_ms | long | Maximum insert search phase ms. |
| max_insert_total_ms | long | Maximum insert total ms. |
| max_insert_update_phase_ms | long | Maximum insert update phase ms. |
| max_key | long | Maximum key. |
| max_node_id | long | Max node identifier. |
| max_operation_duration_ms | long | Maximum operation duration ms. |
| max_overestimation | real | Maximum overestimation. |
| max_query_memory_bytes | long | Max query memory size in bytes. |
| max_query_memory_kb | long | Maximum query memory kb. |
| max_query_memory_pages | long | Maximum query memory pages. |
| max_required_memory_kb_from_plan | long | Maximum required memory kb from plan. |
| max_rowgoalmisestimate | real | Maximum rowgoalmisestimate. |
| max_skewness | real | Maximum skewness. |
| max_tablesize | real | Maximum tablesize. |
| max_target_memory_kb | long | Maximum target memory kb. |
| max_tempdb_space_used_pages | long | Maximum tempdb space used pages. |
| max_tempdb_space_used_percentage | long | Max tempdb space used pe percentage. |
| max_underestimation | real | Maximum underestimation. |
| max_validation_queue_size | long | Maximum validation queue size. |
| max_value | long | Maximum value. |
| maxdop | long | Maxdop. |
| maxdop_one | bool | Boolean flag indicating whether maxdop one. |
| medium_gateway_active_acquires | long | Medium gateway active acquires. |
| medium_gateway_count_waiters | long | Medium gateway count waiters. |
| medium_gateway_threshold | long | Medium gateway threshold. |
| medium_gateway_throughput | long | Medium gateway throughput. |
| memory_allocated_max_kb | long | Memory allocated max kb. |
| memory_allocated_min_kb | long | Memory allocated min kb. |
| memory_allocated_sum_kb | long | Memory allocated sum kb. |
| memory_spilled_kb | long | Memory spilled kb. |
| memory_summary_by_operator_kb | string | Memory summary by operator kb. |
| memory_usage_avg_kb | long | Memory usage avg kb. |
| memory_usage_max_kb | long | Memory usage max kb. |
| memory_usage_min_kb | long | Memory usage min kb. |
| memory_usage_standard_deviation_kb | long | Memory usage standard deviation kb. |
| memory_usage_sum_kb | long | Memory usage sum kb. |
| message_discarded | bool | Boolean flag indicating whether message discarded. |
| message_id | string | Message identifier. |
| min_delete_find_neighbors_phase_ms | long | Minimum delete find neighbors phase ms. |
| min_delete_total_ms | long | Minimum delete total ms. |
| min_delete_update_edges_phase_ms | long | Minimum delete update edges phase ms. |
| min_insert_search_phase_ms | long | Minimum insert search phase ms. |
| min_insert_total_ms | long | Minimum insert total ms. |
| min_insert_update_phase_ms | long | Minimum insert update phase ms. |
| min_operation_duration_ms | long | Minimum operation duration ms. |
| min_query_memory_kb | long | Minimum query memory kb. |
| model_variation | string | Model variation. |
| model_variation_cached | string | Model variation cached. |
| model_variation_current | string | Model variation current. |
| model_variation_new | string | Model variation new. |
| multi_column_density | real | Multi column density. |
| new_filter_strategy | long | New filter strategy. |
| new_join_strategy | long | New join strategy. |
| new_rate | long | New rate. |
| new_rowgoal_strategy | long | New rowgoal strategy. |
| new_value | long | New value. |
| node_height | long | Node height. |
| node_id | long | Node identifier. |
| node_ids | string | Node ids. |
| non_grant_memory_emission_threshold_kb | long | Non grant memory emission threshold kb. |
| non_grant_memory_used_kb | long | Non grant memory used kb. |
| num_filter_preds | long | Num filter preds. |
| number_of_estimated_rows | real | Number of estimated rows. |
| number_of_keys | long | Number of keys. |
| number_of_readOnly_keys | long | Number of read Only keys. |
| number_stale_leaves | long | Number stale leaves. |
| object_id | long | Object identifier. |
| object_name | string | Object name. |
| observed_count | long | Number of observed. |
| old_rate | long | Old rate. |
| old_scan_rows | long | Old scan rows. |
| operation | string | Operation. |
| operation_code | long | Operation code. |
| operation_type | string | Type classification for operation. |
| operator_code | long | Operator code. |
| operator_type_code | long | Operator type code. |
| opt_replay_error_state | long | State value for opt replay error. |
| optional_parameter_optimization_supported | bool | Boolean flag indicating whether optional parameter optimization supported. |
| optional_parameter_predicate_count | long | Number of optional parameter predicate. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| original_cpu_time | long | Original CPU time timestamp. |
| original_data_source_id | long | Original data source identifier. |
| original_file_count | long | Number of original file. |
| original_plan_hash | long | Original plan hash. |
| original_query_plan_hash_signed | long | Original query plan hash signed. |
| original_source_size | long | Original source size. |
| overestimate_count | long | Number of overestimate. |
| overestimate_count_lug | long | Overestimate count lug. |
| overestimate_count_pg | long | Overestimate count pg. |
| overestimate_error_lug_kb | long | Overestimate error lug kb. |
| overestimate_error_pg_kb | long | Overestimate error pg kb. |
| overestimation_nodes | long | Overestimation nodes. |
| package | string | Package. |
| parallel_requested | bool | Boolean flag indicating whether parallel requested. |
| parent_name | string | Parent name. |
| partition_count | long | Number of partition. |
| partition_key_data_type | string | Type classification for partition key data. |
| partition_requested | bool | Boolean flag indicating whether partition requested. |
| persisted_additional_memory_after_kb | long | Persisted additional memory after kb. |
| persisted_additional_memory_before_kb | long | Persisted additional memory before kb. |
| physical_database_guid | string | Physical database guid. |
| physical_operator_id | long | Physical operator identifier. |
| plan_handle | string | Plan handle. |
| plan_id | long | Plan identifier. |
| pool_id | long | Pool identifier. |
| pool_name | string | Pool name. |
| predicate_count | long | Number of predicate. |
| predicate_count_opo | long | Predicate count opo. |
| predicate_count_psp | long | Predicate count psp. |
| predicate_details | string | Predicate details. |
| prev_avg_adjusted_elapsed_time_ms | long | Prev avg adjusted elapsed time ms in milliseconds. |
| prev_avg_cpu_time_ms | long | Prev avg CPU time ms in milliseconds. |
| prev_avg_parallelism_wait_time_ms | long | Prev avg parallelism wait time ms in milliseconds. |
| prev_feedback | long | Prev feedback. |
| prev_feedback_dop | long | Prev feedback dop. |
| prev_leading_col_sort_type | int | Type classification for prev leading col sort. |
| prev_std_dev_adjusted_elapsed_time_ms | long | Prev std dev adjusted elapsed time ms in milliseconds. |
| prev_std_dev_cpu_time_ms | long | Prev std dev CPU time ms in milliseconds. |
| prev_std_dev_parallelism_wait_time_ms | long | Prev std dev parallelism wait time ms in milliseconds. |
| previous_value | long | Previous value. |
| psp_optimization_supported | bool | Boolean flag indicating whether psp optimization supported. |
| quantization_build_time_ms | long | Quantization build time ms in milliseconds. |
| query_cost | real | Query cost. |
| query_dop | long | Query dop. |
| query_hash | long | Query hash. |
| query_hash_signed | long | Query hash signed. |
| query_id | long | Query identifier. |
| query_operator_node_id | long | Query operator node identifier. |
| query_plan_hash | long | Query plan hash. |
| query_plan_hash_signed | long | Query plan hash signed. |
| query_text_hash | string | Query text hash. |
| query_type | long | Type classification for query. |
| query_variant_id | long | Query variant identifier. |
| quick_parallel | long | Quick parallel. |
| quick_serial | long | Quick serial. |
| quickstage_successful | bool | Boolean flag indicating whether quickstage successful. |
| quickstage_time_ms | long | Quickstage time ms in milliseconds. |
| quickstage_useplan_enabled | bool | Boolean flag indicating whether quickstage useplan enabled. |
| r_value | long | R value. |
| reason | string | Reason. |
| recursion_count | long | Number of recursion. |
| regex_selectivity_hints | long | Regex selectivity hints. |
| remaining_file_count | long | Number of remaining file. |
| remaining_source_size | long | Remaining source size. |
| replay_mode | string | Replay mode. |
| request_time | datetime | Request time timestamp. |
| requested_memory_kb | long | Requested memory kb. |
| required_exchange_memory_kb | long | Required exchange memory kb. |
| required_memory_kb | long | Required memory kb. |
| required_serial_bulkinsert_memory_kb | long | Required serial bulkinsert memory kb. |
| resource_group_id | long | Resource group identifier. |
| resource_group_name | string | Resource group name. |
| resource_pool_id | long | Resource pool identifier. |
| resource_pool_name | string | Resource pool name. |
| retries | long | Retries. |
| reused_workfiles | long | Reused workfiles. |
| row_threshold | long | Row threshold. |
| rowgoalmisestimation_nodes | long | Rowgoalmisestimation nodes. |
| rows_processed_delta_count | long | Number of rows processed delta. |
| rows_processed_per_run | long | Rows processed per run. |
| runtime_reassessment_execution_count | long | Number of runtime reassessment execution. |
| sample_percentage | long | Sample pe percentage. |
| schema_name | string | Schema name. |
| search_time_delta_ms | long | Search time delta ms in milliseconds. |
| serial_plan | bool | Boolean flag indicating whether serial plan. |
| sessionName | string | Session Name. |
| session_id | long | Session identifier. |
| small_gateway_active_acquires | long | Small gateway active acquires. |
| small_gateway_count_waiters | long | Small gateway count waiters. |
| small_gateway_threshold | long | Small gateway threshold. |
| small_gateway_throughput | long | Small gateway throughput. |
| smallest_single_column_density | real | Smallest single column density. |
| sort_operation_type | long | Type classification for sort operation. |
| spill_count | long | Number of spill. |
| spill_count_lug | long | Spill count lug. |
| spill_count_pg | long | Spill count pg. |
| spill_error_lug_kb | long | Spill error lug kb. |
| spill_error_pg_kb | long | Spill error pg kb. |
| spill_sum_kb | long | Spill sum kb. |
| split_count | long | Number of split. |
| stabilized_avg_adjusted_elapsed_time_ms | long | Stabilized avg adjusted elapsed time ms in milliseconds. |
| stabilized_avg_cpu_time_ms | long | Stabilized avg CPU time ms in milliseconds. |
| stabilized_avg_parallelism_wait_time_ms | long | Stabilized avg parallelism wait time ms in milliseconds. |
| stabilized_feedback_dop | long | Stabilized feedback dop. |
| stabilized_std_dev_adjusted_elapsed_time_ms | long | Stabilized std dev adjusted elapsed time ms in milliseconds. |
| stabilized_std_dev_cpu_time_ms | long | Stabilized std dev CPU time ms in milliseconds. |
| stabilized_std_dev_parallelism_wait_time_ms | long | Stabilized std dev parallelism wait time ms in milliseconds. |
| state | long | Current lifecycle or health state. |
| state_new | long | State new. |
| state_old | long | State old. |
| statement_key_hash | long | Statement key hash. |
| statement_number | long | Statement number. |
| statement_sql_handle | string | Statement SQL handle. |
| statement_sql_hash | string | Statement SQL hash. |
| statistics_list | string | Statistics list. |
| stats_column_count | long | Number of stats column. |
| stats_columns_conjunct_count | long | Number of stats columns conjunct. |
| stats_columns_filter_count | long | Number of stats columns filter. |
| stats_id | long | Stats identifier. |
| stats_update_correlation_id | string | Stats update correlation identifier. |
| status | string | Current status reported by the component. |
| std_dev_adjusted_elapsed_time_ms | long | Std dev adjusted elapsed time ms in milliseconds. |
| std_dev_cpu_time_ms | long | Std dev CPU time ms in milliseconds. |
| std_dev_parallelism_wait_time_ms | long | Std dev parallelism wait time ms in milliseconds. |
| stdev_cpu_time | long | Stdev CPU time timestamp. |
| stmt_count | long | Number of stmt. |
| stmt_type | long | Type classification for stmt. |
| success | bool | Boolean flag indicating whether success. |
| successful_task_count | long | Number of successful task. |
| table_cardinality | real | Table cardinality. |
| table_id | long | Table identifier. |
| table_name | string | Table name. |
| target_memory_kb | long | Target memory kb. |
| tasks_count | long | Number of tasks. |
| thread_count | long | Number of thread. |
| thread_id | long | Thread identifier. |
| threshold_type | string | Type classification for threshold. |
| time_out | bool | Boolean flag indicating whether time out. |
| time_ticks | long | Time ticks. |
| timeout_error_count | long | Number of timeout error. |
| timeout_sec | long | Timeout sec. |
| total_available_memory_kb | long | Total available memory kb. |
| total_build_time_ms | long | Total build time ms. |
| total_compilations | long | Total compilations. |
| total_conjunct_count | long | Number of total conjunct. |
| total_duration_ms | long | Total duration ms. |
| total_execution_count | long | Number of total execution. |
| total_granted_memory_kb | long | Total granted memory kb. |
| total_grantee_count | long | Number of total grantee. |
| total_hash_agg_memory_bytes | long | Total hash agg memory size in bytes. |
| total_max_memory_kb | long | Total max memory kb. |
| total_memory_kb | long | Total memory kb. |
| total_nodes | long | Total nodes. |
| total_pages | long | Total pages. |
| total_rows_count | long | Number of total rows. |
| total_rows_processed | long | Total rows processed. |
| total_runs | long | Total runs. |
| total_search_time_ms | long | Total search time ms. |
| total_update_count | long | Number of total update. |
| total_update_time_ms | long | Total update time ms. |
| total_vectors_deleted | long | Total vectors deleted. |
| total_vectors_inserted | long | Total vectors inserted. |
| total_waiter_count | long | Number of total waiter. |
| total_workfiles | long | Total workfiles. |
| tp_parallel | long | Tp parallel. |
| tp_serial | long | Tp serial. |
| trivial_plan | long | Trivial plan. |
| trivial_plan_scanning_cs_index_discarded | long | Trivial plan scanning cs index discarded. |
| tsql_frame | string | Tsql frame. |
| udf_name | string | Udf name. |
| underestimation_nodes | long | Underestimation nodes. |
| update_time_delta_ms | long | Update time delta ms in milliseconds. |
| used_cache_size | long | Used cache size. |
| used_memory_kb | long | Used memory kb. |
| useplan_successful | bool | Boolean flag indicating whether useplan successful. |
| validation_queue_size | long | Validation queue size. |
| value | long | Value. |
| vector_distance_metric | string | Vector distance metric. |
| vector_index_column_name | string | Vector index column name. |
| vector_index_id | long | Vector index identifier. |
| vector_index_type | string | Type classification for vector index. |
| virtual_column_count | long | Number of virtual column. |
| virtual_columns_conjunct_count | long | Number of virtual columns conjunct. |
| virtual_columns_referenced | string | Virtual columns referenced. |
| virtual_columns_replacement_count | long | Number of virtual columns replacement. |
| wait_time_sec | long | Wait time sec. |
| waiter_count | long | Number of waiter. |
| xml_compression_time_ms | long | Xml compression time ms in milliseconds. |
| xml_data_compressed_bytes | long | Xml data compressed size in bytes. |
| xml_data_uncompressed_bytes | long | Xml data uncompressed size in bytes. |

## MonQueryStoreFailures — Query Store Failures

**Purpose**: Query Store Failures. Used to investigate slow queries, waits, blocking, deadlocks, and Query Store behavior. Referenced in MI template areas: performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| code_package_version | string | Code package version. |
| column_id | long | Column identifier. |
| config_version | long | Config version. |
| current_buffered_items_size_kb | long | Current buffered items size kb. |
| current_hash_based_hints_map_entries_count | long | Number of current hash based hints map entries. |
| current_instance_total_resource_size_kb | long | Current instance total resource size kb. |
| current_size_kb | long | Current size kb. |
| current_stmt_hash_map_size_kb | long | Current stmt hash map size kb. |
| current_template_param_hints_hash_map_entries_count | long | Number of current template param hints hash map entries. |
| current_template_param_hints_hash_map_size_kb | long | Current template param hints hash map size kb. |
| cursor_populate_fingerprint | long | Cursor populate fingerprint. |
| database_id | long | Database identifier. |
| diagnostic_info | string | Diagnostic info. |
| error_count | long | Number of error. |
| error_number | long | SQL or platform error number. |
| error_severity | long | Error severity. |
| error_state | long | State value for error. |
| event | string | Event name emitted by the component. |
| exception_catch_context | string | Exception catch context. |
| group_name | string | Group name. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| initiator | long | Initiator. |
| internal_table_type | long | Type classification for internal table. |
| logical_database_guid | string | Logical database guid. |
| logical_database_name | string | Logical database name. |
| max_buffered_items_size_kb | long | Maximum buffered items size kb. |
| max_instance_total_resource_size_kb | long | Maximum instance total resource size kb. |
| max_memory_available_kb | long | Maximum memory available kb. |
| max_resource_available_kb | long | Maximum resource available kb. |
| max_size_kb | long | Maximum size kb. |
| max_stmt_hash_map_size_kb | long | Maximum stmt hash map size kb. |
| max_template_param_hints_hash_map_entries_count | long | Number of max template param hints hash map entries. |
| memory_percentage_limit | long | Memory percentage limit. |
| object_id | long | Object identifier. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| parent_query_hash | long | Parent query hash. |
| plan_fingerprint | long | Plan fingerprint. |
| plan_id | long | Plan identifier. |
| query_hint_id | long | Query hint identifier. |
| query_hint_text | string | Query hint text. |
| query_id | long | Query identifier. |
| query_store_resource_type | string | Type classification for query store resource. |
| query_variant_hash | long | Query variant hash. |
| reason | string | Reason. |
| sessionName | string | Session Name. |
| source_database_id | long | Source database identifier. |
| status | long | Current status reported by the component. |
| subtype | long | Subtype. |
| task_type | long | Type classification for task. |
| type | long | Type. |

## MonQueryStoreInfo — Query Store Info

**Purpose**: Query Store Info. Used to investigate slow queries, waits, blocking, deadlocks, and Query Store behavior. Referenced in MI template areas: performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| abort_duration | long | Abort duration. |
| abort_wait_abort_retry_count | long | Number of abort wait abort retry. |
| abort_wait_retry_count | long | Number of abort wait retry. |
| backoffs | long | Backoffs. |
| capture_policy_execution_count | long | Number of capture policy execution. |
| capture_policy_execution_count_new | long | Capture policy execution count new. |
| capture_policy_execution_count_old | long | Capture policy execution count old. |
| capture_policy_mode | string | Capture policy mode. |
| capture_policy_mode_new | string | Capture policy mode new. |
| capture_policy_mode_old | string | Capture policy mode old. |
| capture_policy_stale_threshold_hours | long | Capture policy stale threshold hours. |
| capture_policy_stale_threshold_hours_new | long | Capture policy stale threshold hours new. |
| capture_policy_stale_threshold_hours_old | long | Capture policy stale threshold hours old. |
| capture_policy_total_compile_cpu_ms | long | Capture policy total compile CPU ms in milliseconds. |
| capture_policy_total_compile_cpu_ms_new | long | Capture policy total compile CPU ms new. |
| capture_policy_total_compile_cpu_ms_old | long | Capture policy total compile CPU ms old. |
| capture_policy_total_execution_cpu_ms | long | Capture policy total execution CPU ms in milliseconds. |
| capture_policy_total_execution_cpu_ms_new | long | Capture policy total execution CPU ms new. |
| capture_policy_total_execution_cpu_ms_old | long | Capture policy total execution CPU ms old. |
| clear_all | bool | Boolean flag indicating whether clear all. |
| code_package_version | string | Code package version. |
| collisions | long | Collisions. |
| context_settings_memory_usage_kb | long | Context settings memory usage kb. |
| current_buffered_items_size_kb | long | Current buffered items size kb. |
| current_hash_based_hints_map_entries_count | long | Number of current hash based hints map entries. |
| current_instance_total_resource_size_kb | long | Current instance total resource size kb. |
| current_partitioned_heap_size_kb | long | Current partitioned heap size kb. |
| current_size_kb | long | Current size kb. |
| current_stmt_hash_map_size_kb | long | Current stmt hash map size kb. |
| current_template_param_hints_hash_map_entries_count | long | Number of current template param hints hash map entries. |
| current_template_param_hints_hash_map_size_kb | long | Current template param hints hash map size kb. |
| database_id | long | Database identifier. |
| db_state_actual | long | Database state actual. |
| db_state_desired | long | Database state desired. |
| deleted_plan_count | long | Number of deleted plan. |
| deleted_query_count | long | Number of deleted query. |
| delta_max_cpu_time | long | Delta max CPU time timestamp. |
| delta_max_elapsed_time | long | Delta max elapsed time timestamp. |
| delta_max_items_in_queue | long | Delta max items in queue. |
| delta_max_items_in_waiting_queue | long | Delta max items in waiting queue. |
| delta_max_time_in_queue | long | Delta max time in queue. |
| delta_max_time_in_waiting_queue | long | Delta max time in waiting queue. |
| delta_total_cpu_time | long | Delta total CPU time timestamp. |
| delta_total_elapsed_time | long | Delta total elapsed time timestamp. |
| delta_total_failure_count | long | Number of delta total failure. |
| delta_total_items_in_queue | long | Delta total items in queue. |
| delta_total_items_in_waiting_queue | long | Delta total items in waiting queue. |
| delta_total_success_count | long | Number of delta total success. |
| delta_total_time_in_queue | long | Delta total time in queue. |
| delta_total_time_in_waiting_queue | long | Delta total time in waiting queue. |
| error_number | long | SQL or platform error number. |
| error_severity | long | Error severity. |
| error_state | long | State value for error. |
| estimated_deleted_size_kb | long | Estimated deleted size kb. |
| event | string | Event name emitted by the component. |
| fast_path_optimization_mode | string | Fast path optimization mode. |
| fast_path_optimization_mode_new | string | Fast path optimization mode new. |
| fast_path_optimization_mode_old | string | Fast path optimization mode old. |
| flush_interval_seconds | long | Flush interval seconds. |
| flush_interval_seconds_new | long | Flush interval seconds new. |
| flush_interval_seconds_old | long | Flush interval seconds old. |
| forwarded_messages_count | long | Number of forwarded messages. |
| global_mem_obj_size_kb | long | Global memory obj size kb. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| instance_total_resource_read_write_target_kb | long | Instance total resource read write target kb. |
| interval_length_minutes | long | Interval length minutes. |
| interval_length_minutes_new | long | Interval length minutes new. |
| interval_length_minutes_old | long | Interval length minutes old. |
| is_flushed | bool | Boolean flag indicating whether flushed. |
| is_forced_plan | bool | Boolean flag indicating whether forced plan. |
| is_hash_based_hint | bool | Boolean flag indicating whether hash based hint. |
| is_removed | bool | Boolean flag indicating whether removed. |
| is_send_queue | bool | Boolean flag indicating whether send queue. |
| is_user_initiated | bool | Boolean flag indicating whether user initiated. |
| item_type | long | Type classification for item. |
| last_deleted_query_total_cpu | long | Last deleted query total CPU. |
| logical_database_guid | string | Logical database guid. |
| logical_database_name | string | Logical database name. |
| matching_queries_count | long | Number of matching queries. |
| max_buffered_items_size_kb | long | Maximum buffered items size kb. |
| max_cpu_time | long | Max CPU time timestamp. |
| max_deleted_total_cpu | long | Maximum deleted total CPU. |
| max_elapsed_time | long | Max elapsed time timestamp. |
| max_instance_total_resource_size_kb | long | Maximum instance total resource size kb. |
| max_items_in_queue | long | Maximum items in queue. |
| max_items_in_waiting_queue | long | Maximum items in waiting queue. |
| max_memory_available_kb | long | Maximum memory available kb. |
| max_plans_per_query | long | Maximum plans per query. |
| max_plans_per_query_new | long | Maximum plans per query new. |
| max_plans_per_query_old | long | Maximum plans per query old. |
| max_size_kb | long | Maximum size kb. |
| max_size_mb | long | Maximum size mb. |
| max_size_mb_new | long | Maximum size mb new. |
| max_size_mb_old | long | Maximum size mb old. |
| max_stmt_hash_map_size_kb | long | Maximum stmt hash map size kb. |
| max_template_param_hints_hash_map_entries_count | long | Number of max template param hints hash map entries. |
| max_time_in_queue | long | Maximum time in queue. |
| max_time_in_waiting_queue | long | Maximum time in waiting queue. |
| memory_percentage_limit | long | Memory percentage limit. |
| messaging_discarded_message_count | long | Number of messaging discarded message. |
| messaging_internal_max_threshold | long | Messaging internal max threshold. |
| messaging_memory_used_mb | long | Messaging memory used mb. |
| min_repeat_period_seconds | long | Minimum repeat period seconds. |
| new_plan_forcing_type | string | Type classification for new plan forcing. |
| object_id | long | Object identifier. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| pending_message_count | long | Number of pending message. |
| pending_persistance_memory_usage_kb | long | Pending persistance memory usage kb. |
| plan_count | long | Number of plan. |
| plan_forcing_mode | string | Plan forcing mode. |
| plan_forcing_mode_new | string | Plan forcing mode new. |
| plan_forcing_mode_old | string | Plan forcing mode old. |
| plan_id | long | Plan identifier. |
| plans_used_last_day | long | Plans used last day. |
| plans_used_last_hour | long | Plans used last hour. |
| processed_messages_count | long | Number of processed messages. |
| queries_used_last_day | long | Queries used last day. |
| queries_used_last_hour | long | Queries used last hour. |
| query_cost | real | Query cost. |
| query_count | long | Number of query. |
| query_hash | long | Query hash. |
| query_hash_matched_stmt | long | Query hash matched stmt. |
| query_hint_id | long | Query hint identifier. |
| query_hint_text | string | Query hint text. |
| query_id | long | Query identifier. |
| query_id_matched_stmt | long | Query id matched stmt. |
| query_store_enabled_new | bool | Boolean flag indicating whether query store enabled new. |
| query_store_enabled_old | bool | Boolean flag indicating whether query store enabled old. |
| query_store_error_state_new | bool | Boolean flag indicating whether query store error state new. |
| query_store_error_state_old | bool | Boolean flag indicating whether query store error state old. |
| query_store_read_only_new | bool | Boolean flag indicating whether query store read only new. |
| query_store_read_only_old | bool | Boolean flag indicating whether query store read only old. |
| query_store_read_only_reason | long | Query store read only reason. |
| query_store_resource_type | string | Type classification for query store resource. |
| query_text_count | long | Number of query text. |
| query_text_id | long | Query text identifier. |
| query_text_id_matched_stmt | long | Query text id matched stmt. |
| query_tuning_mode | string | Query tuning mode. |
| query_tuning_mode_new | string | Query tuning mode new. |
| query_tuning_mode_old | string | Query tuning mode old. |
| read_write_percentage_target | long | Read write percentage target. |
| runtime_stats_cache_store_bucket_count | long | Number of runtime stats cache store bucket. |
| runtime_stats_memory_usage_kb | long | Runtime stats memory usage kb. |
| sessionName | string | Session Name. |
| size_based_cleanup_mode | string | Size based cleanup mode. |
| size_based_cleanup_mode_new | string | Size based cleanup mode new. |
| size_based_cleanup_mode_old | string | Size based cleanup mode old. |
| size_based_cleanup_percent_target | long | Size based cleanup percentage target. |
| size_based_cleanup_percent_trigger | long | Size based cleanup percentage trigger. |
| sleep_time_ms | long | Sleep time ms in milliseconds. |
| spinlock_type | string | Type classification for spinlock. |
| spins | long | Spins. |
| stale_query_threshold_days | long | Stale query threshold days. |
| stale_query_threshold_days_new | long | Stale query threshold days new. |
| stale_query_threshold_days_old | long | Stale query threshold days old. |
| statement_sql_hash | string | Statement SQL hash. |
| statement_sql_hash_matched_stmt | string | Statement SQL hash matched stmt. |
| stmt_hash_map_read_write_target_kb | long | Stmt hash map read write target kb. |
| target_delete_size_kb | long | Target delete size kb. |
| task_type | long | Type classification for task. |
| task_type_name | string | Task type name. |
| ticks_per_second | long | Ticks per second. |
| time_since_last_cleanup_seconds | long | Time since last cleanup seconds. |
| total_cpu_time | long | Total CPU time timestamp. |
| total_elapsed_time | long | Total elapsed time timestamp. |
| total_failure_count | long | Number of total failure. |
| total_items_cleared_in_the_queue | long | Total items cleared in the queue. |
| total_items_in_queue | long | Total items in queue. |
| total_items_in_waiting_queue | long | Total items in waiting queue. |
| total_success_count | long | Number of total success. |
| total_time_in_queue | long | Total time in queue. |
| total_time_in_waiting_queue | long | Total time in waiting queue. |
| undecided_queries_window_duration_minutes | long | Undecided queries window duration minutes. |
| undecided_query_count | long | Number of undecided query. |
| wait_stats_capture_mode | string | Wait stats capture mode. |
| wait_stats_capture_mode_new | string | Wait stats capture mode new. |
| wait_stats_capture_mode_old | string | Wait stats capture mode old. |

## MonSqlTransactions — SQL Transactions

**Purpose**: SQL Transactions. Used to investigate slow queries, waits, blocking, deadlocks, and Query Store behavior. Referenced in MI template areas: performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| aborted_version_cleaner_end_time | datetime | Aborted version cleaner end time timestamp. |
| aborted_version_cleaner_start_time | datetime | Aborted version cleaner start time timestamp. |
| addl_allocation_sessions_created | long | Addl allocation sessions created. |
| adr_mtvc2_worker_record_skip_btree_disconnected | long | Adr mtvc2 worker record skip btree disconnected. |
| adr_mtvc2_worker_record_skip_none | long | Adr mtvc2 worker record skip none. |
| adr_mtvc2_worker_record_skip_page_not_allocated | long | Adr mtvc2 worker record skip page not allocated. |
| adr_mtvc2_worker_record_skip_row_lock | long | Adr mtvc2 worker record skip row lock. |
| adr_mtvc2_worker_record_skip_slot_modification | long | Adr mtvc2 worker record skip slot modification. |
| adr_mtvc2_worker_record_skip_stub_page_lock | long | Adr mtvc2 worker record skip stub page lock. |
| adr_mtvc2_worker_record_skip_unknown | long | Adr mtvc2 worker record skip unknown. |
| adr_mtvc2_worker_sweep_pages_skipped_alloc_unit_dropped | long | Adr mtvc2 worker sweep pages skipped alloc unit dropped. |
| adr_mtvc2_worker_sweep_pages_skipped_buf_latch_timeout | long | Adr mtvc2 worker sweep pages skipped buf latch timeout. |
| adr_mtvc2_worker_sweep_pages_skipped_hobt_lock_not_found | long | Adr mtvc2 worker sweep pages skipped hobt lock not found. |
| adr_mtvc2_worker_sweep_pages_skipped_hobt_locks_not_taken | long | Adr mtvc2 worker sweep pages skipped hobt locks not taken. |
| adr_mtvc2_worker_sweep_pages_skipped_oom | long | Adr mtvc2 worker sweep pages skipped OOM. |
| adr_mtvc2_worker_sweep_pages_skipped_out_of_disk | long | Adr mtvc2 worker sweep pages skipped out of disk. |
| adr_mtvc2_worker_sweep_pages_skipped_page_locks | long | Adr mtvc2 worker sweep pages skipped page locks. |
| adr_mtvc2_worker_sweep_pages_skipped_pvs_rowset | long | Adr mtvc2 worker sweep pages skipped pvs rowset. |
| adr_mtvc2_worker_sweep_pages_skipped_resumable_locks | long | Adr mtvc2 worker sweep pages skipped resumable locks. |
| adr_non_data_pages_swept | long | Adr non data pages swept. |
| adr_pages_cold_read | long | Adr pages cold read. |
| adr_pages_io_wait_time | long | Adr pages I/O wait time timestamp. |
| adr_pages_reads_in_progress | long | Adr pages reads in progress. |
| adr_pages_swept | long | Adr pages swept. |
| adr_pages_swept_marked_no_versions | long | Adr pages swept marked no versions. |
| adr_sweep_pages_skipped_alloc_unit_dropped | long | Adr sweep pages skipped alloc unit dropped. |
| adr_sweep_pages_skipped_buf_latch_timeout | long | Adr sweep pages skipped buf latch timeout. |
| adr_sweep_pages_skipped_hobt_lock_not_found | long | Adr sweep pages skipped hobt lock not found. |
| adr_sweep_pages_skipped_hobt_locks_not_taken | long | Adr sweep pages skipped hobt locks not taken. |
| adr_sweep_pages_skipped_oom | long | Adr sweep pages skipped OOM. |
| adr_sweep_pages_skipped_out_of_disk | long | Adr sweep pages skipped out of disk. |
| adr_sweep_pages_skipped_page_locks | long | Adr sweep pages skipped page locks. |
| adr_sweep_pages_skipped_pvs_rowset | long | Adr sweep pages skipped pvs rowset. |
| adr_sweep_pages_skipped_resumable_locks | long | Adr sweep pages skipped resumable locks. |
| adr_tx_rollback_count | long | Number of adr tx rollback. |
| alloc_unit_id_populate_chainlength_max | long | Alloc unit id populate chainlength max. |
| alloc_unit_id_populate_duration_max | long | Alloc unit id populate duration max. |
| alloc_unit_type | long | Type classification for alloc unit. |
| allocation_unit_id | long | Allocation unit identifier. |
| au_clean_continued_AU_is_not_empty | long | Au clean continued AU is not empty. |
| au_clean_continued_IAM_is_not_empty | long | Au clean continued IAM is not empty. |
| au_clean_continued_unable_to_lock_IAM_page | long | Au clean continued unable to lock IAM page. |
| au_clean_continued_unable_to_lock_au | long | Au clean continued unable to lock au. |
| au_clean_continued_unable_to_lock_data_page | long | Au clean continued unable to lock data page. |
| au_clean_continued_unable_to_lock_extent | long | Au clean continued unable to lock extent. |
| au_clean_deferred_to_next_run | long | Au clean deferred to next run. |
| au_clean_failed_IAM_is_in_DEFUNCT_file | long | Au clean failed IAM is in DEFUNCT file. |
| au_clean_failed_db_single_user_mode | long | Au clean failed database single user mode. |
| au_clean_failed_exceptions | long | Au clean failed exceptions. |
| au_clean_failed_unable_to_lock_au | long | Au clean failed unable to lock au. |
| au_cleaned | long | Au cleaned. |
| average_background_allocation_factor | long | Average background allocation factor. |
| avg_fragmentation_in_percent | real | Average fragmentation in percentage. |
| avg_fragmentation_in_percent_for_sweep | real | Average fragmentation in percentage for sweep. |
| avg_free_bytes_per_page | real | Average free size in bytes per page. |
| avg_free_bytes_per_page_excluding_fill_factor | real | Average free size in bytes per page excluding fill factor. |
| avg_free_bytes_per_page_excluding_fill_factor_for_sweep | real | Average free size in bytes per page excluding fill factor for sweep. |
| avg_free_bytes_per_page_for_sweep | real | Average free size in bytes per page for sweep. |
| avg_page_space_used_in_percent | real | Average page space used in percentage. |
| avg_page_space_used_in_percent_for_sweep | real | Average page space used in percentage for sweep. |
| avg_row_size | real | Average row size. |
| blob_inserts_off_row_version_info | long | Blob inserts off row version info. |
| chain_length | long | Chain length. |
| chained_row_insert_count | long | Number of chained row insert. |
| code_package_version | string | Code package version. |
| compat_level | long | Compat level. |
| correlation_id | string | Correlation identifier used across components. |
| ctr_non_data_pages_swept | long | Ctr non data pages swept. |
| ctr_pages_cold_read | long | Ctr pages cold read. |
| ctr_pages_io_wait_time | long | Ctr pages I/O wait time timestamp. |
| ctr_pages_reads_in_progress | long | Ctr pages reads in progress. |
| ctr_pages_swept | long | Ctr pages swept. |
| ctr_pages_swept_marked_no_versions | long | Ctr pages swept marked no versions. |
| ctr_tx_rollback_count | long | Number of ctr tx rollback. |
| current_abort_count | long | Number of current abort. |
| database_id | long | Database identifier. |
| database_name | string | Database name. |
| defrag_attempts | long | Defrag attempts. |
| defrag_completed | long | Defrag completed. |
| defrag_skipped_checkdb_checktable | long | Defrag skipped checkdb checktable. |
| defrag_skipped_db_snapshot | long | Defrag skipped database snapshot. |
| defrag_skipped_issue_getting_next_page | long | Defrag skipped issue getting next page. |
| defrag_skipped_ix_lock_failed | long | Defrag skipped ix lock failed. |
| defrag_skipped_large_atm_count | long | Number of defrag skipped large atm. |
| defrag_skipped_large_pvs_size | long | Defrag skipped large pvs size. |
| defrag_skipped_latch_timeout | long | Defrag skipped latch timeout. |
| defrag_skipped_lock_timeout | long | Defrag skipped lock timeout. |
| defrag_skipped_minimal_logging | long | Defrag skipped minimal logging. |
| defrag_skipped_no_estimated_rows_to_move | long | Defrag skipped no estimated rows to move. |
| defrag_skipped_no_page_to_the_right | long | Defrag skipped no page to the right. |
| defrag_skipped_not_enough_space_on_left_page | long | Defrag skipped not enough space on left page. |
| defrag_skipped_other | long | Defrag skipped other. |
| defrag_skipped_out_of_disk_space | long | Defrag skipped out of disk space. |
| defrag_skipped_page_deallocated | long | Defrag skipped page deallocated. |
| defrag_skipped_page_for_system_table | long | Defrag skipped page for system table. |
| defrag_skipped_page_locking_disabled | long | Defrag skipped page locking disabled. |
| defrag_skipped_shrink_lock_failed | long | Defrag skipped shrink lock failed. |
| defrag_skipped_zero_slot_count | long | Number of defrag skipped zero slot. |
| deletes_in_ddl_transaction | long | Deletes in ddl transaction. |
| do_only_lr_count | long | Number of do only lr. |
| duration_ms | long | Duration in milliseconds. |
| empty_pages | long | Empty pages. |
| empty_slots | long | Empty slots. |
| error_code | long | Numeric error code for the failure or event. |
| event | string | Event name emitted by the component. |
| extent_deallocated_later_in_user_tran | long | Extent deallocated later in user tran. |
| extent_deallocated_skipped_exception_in_user_tran | long | Extent deallocated skipped exception in user tran. |
| extent_deallocation_skipped_in_sys_tran | long | Extent deallocation skipped in sys tran. |
| fill_factor | long | Fill factor. |
| foreground_allocation_percent | long | Foreground allocation percentage. |
| fragment_count | long | Number of fragment. |
| free_space | long | Free space. |
| free_space_excluding_fill_factor | long | Free space excluding fill factor. |
| free_space_excluding_fill_factor_for_sweep | long | Free space excluding fill factor for sweep. |
| free_space_for_sweep | long | Free space for sweep. |
| gam_concurrent_update_count | long | Number of gam concurrent update. |
| gam_exclusive_update_count | long | Number of gam exclusive update. |
| gam_exclusive_update_non_locked_count | long | Number of gam exclusive update non locked. |
| gam_exclusive_update_non_logged_count | long | Number of gam exclusive update non logged. |
| gam_sh_write_latch_count | long | Number of gam sh write latch. |
| gam_up_latch_count | long | Number of gam up latch. |
| ghost_cleanup_pages_skipped_bulk_temp_page_not_removable | long | Ghost cleanup pages skipped bulk temp page not removable. |
| ghost_cleanup_pages_skipped_last_ghost_not_removable | long | Ghost cleanup pages skipped last ghost not removable. |
| ghost_cleanup_pages_skipped_last_page_btree | long | Ghost cleanup pages skipped last page btree. |
| ghost_cleanup_pages_skipped_no_ghost_removable | long | Ghost cleanup pages skipped no ghost removable. |
| ghost_cleanup_pages_skipped_no_ghosts | long | Ghost cleanup pages skipped no ghosts. |
| ghost_cleanup_pages_skipped_not_hobt | long | Ghost cleanup pages skipped not hobt. |
| ghost_cleanup_pages_skipped_page_locks | long | Ghost cleanup pages skipped page locks. |
| ghost_cleanup_pages_skipped_page_not_empty | long | Ghost cleanup pages skipped page not empty. |
| ghost_cleanup_pages_skipped_unknown | long | Ghost cleanup pages skipped unknown. |
| ghost_cleanup_records_cleaned | long | Ghost cleanup records cleaned. |
| ghost_cleanup_records_skipped_after_aborted_transaction | long | Ghost cleanup records skipped after aborted transaction. |
| ghost_cleanup_records_skipped_after_oldest_active_transaction | long | Ghost cleanup records skipped after oldest active transaction. |
| ghost_cleanup_records_skipped_after_oldest_snapshot | long | Ghost cleanup records skipped after oldest snapshot. |
| ghost_cleanup_records_skipped_commit_after_min_useful_transacti | long | Ghost cleanup records skipped commit after min useful transacti. |
| ghost_cleanup_records_skipped_lock_acquisition | long | Ghost cleanup records skipped lock acquisition. |
| ghost_cleanup_records_skipped_low_watermark | long | Ghost cleanup records skipped low watermark. |
| ghost_cleanup_records_skipped_page | long | Ghost cleanup records skipped page. |
| ghost_cleanup_records_skipped_page_not_allocated | long | Ghost cleanup records skipped page not allocated. |
| ghost_cleanup_records_skipped_record_dam | long | Ghost cleanup records skipped record dam. |
| ghost_cleanup_records_skipped_transaction_not_cleaned | long | Ghost cleanup records skipped transaction not cleaned. |
| ghost_cleanup_records_skipped_unknown | long | Ghost cleanup records skipped unknown. |
| ghost_page_cleanup_skipped_bulk_temp_page_not_removable | long | Ghost page cleanup skipped bulk temp page not removable. |
| ghost_page_cleanup_skipped_last_ghost_not_removable | long | Ghost page cleanup skipped last ghost not removable. |
| ghost_page_cleanup_skipped_last_page_btree | long | Ghost page cleanup skipped last page btree. |
| ghost_page_cleanup_skipped_no_ghost_removable | long | Ghost page cleanup skipped no ghost removable. |
| ghost_page_cleanup_skipped_no_ghosts | long | Ghost page cleanup skipped no ghosts. |
| ghost_page_cleanup_skipped_not_hobt | long | Ghost page cleanup skipped not hobt. |
| ghost_page_cleanup_skipped_page_changed_btree | long | Ghost page cleanup skipped page changed btree. |
| ghost_page_cleanup_skipped_page_locks | long | Ghost page cleanup skipped page locks. |
| ghost_page_cleanup_skipped_unknown | long | Ghost page cleanup skipped unknown. |
| ghost_pages_attempted_to_clean_by_ghost_cleaner | long | Ghost pages attempted to clean by ghost cleaner. |
| ghost_pages_attempted_to_clean_by_version_cleaner | long | Ghost pages attempted to clean by version cleaner. |
| ghost_pages_fully_cleaned_by_version_cleaner | long | Ghost pages fully cleaned by version cleaner. |
| ghost_pages_partially_cleaned_by_version_cleaner | long | Ghost pages partially cleaned by version cleaner. |
| ghost_pages_proceessed_by_main_thread_of_version_cleaner | long | Ghost pages proceessed by main thread of version cleaner. |
| ghost_pages_skipped_by_version_cleaner | long | Ghost pages skipped by version cleaner. |
| ghost_pages_skipped_by_worker_already_cleaned | long | Ghost pages skipped by worker already cleaned. |
| ghost_pages_skipped_feature_disabled | long | Ghost pages skipped feature disabled. |
| ghost_pages_with_version_bit_set | long | Ghost pages with version bit set. |
| ghost_record_count | long | Number of ghost record. |
| ghost_records_cleaned | long | Ghost records cleaned. |
| ghost_records_cleaned_by_ghost_cleaner | long | Ghost records cleaned by ghost cleaner. |
| ghost_records_cleaned_by_stmt_cleanup | long | Ghost records cleaned by stmt cleanup. |
| ghost_records_cleaned_by_version_cleaner | long | Ghost records cleaned by version cleaner. |
| ghost_records_cleanup_skipped_after_aborted_transaction | long | Ghost records cleanup skipped after aborted transaction. |
| ghost_records_cleanup_skipped_after_oldest_active_transaction | long | Ghost records cleanup skipped after oldest active transaction. |
| ghost_records_cleanup_skipped_after_oldest_snapshot | long | Ghost records cleanup skipped after oldest snapshot. |
| ghost_records_cleanup_skipped_commit_after_min_useful_transacti | long | Ghost records cleanup skipped commit after min useful transacti. |
| ghost_records_cleanup_skipped_lock_acquisition | long | Ghost records cleanup skipped lock acquisition. |
| ghost_records_cleanup_skipped_low_watermark | long | Ghost records cleanup skipped low watermark. |
| ghost_records_cleanup_skipped_page | long | Ghost records cleanup skipped page. |
| ghost_records_cleanup_skipped_page_not_allocated | long | Ghost records cleanup skipped page not allocated. |
| ghost_records_cleanup_skipped_record_dam | long | Ghost records cleanup skipped record dam. |
| ghost_records_cleanup_skipped_transaction_not_cleaned | long | Ghost records cleanup skipped transaction not cleaned. |
| ghost_records_cleanup_skipped_unknown | long | Ghost records cleanup skipped unknown. |
| heap_deforwarding_count | long | Number of heap deforwarding. |
| hobt_id | long | Hobt identifier. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| iam_cache_lookup_alloc_or_dealloc_count | long | Number of iam cache lookup alloc or dealloc. |
| iam_cache_lookup_allocation_order_scan_count | long | Number of iam cache lookup allocation order scan. |
| iam_cache_lookup_append_only_store_count | long | Number of iam cache lookup append only store. |
| iam_cache_lookup_blob_scan_count | long | Number of iam cache lookup blob scan. |
| iam_cache_lookup_cache_only_page_scanner_count | long | Number of iam cache lookup cache only page scanner. |
| iam_cache_lookup_dbcc_check_count | long | Number of iam cache lookup dbcc check. |
| iam_cache_lookup_fix_page_not_thru_linkage_count | long | Number of iam cache lookup fix page not thru linkage. |
| iam_cache_lookup_ghost_cleaner_count | long | Number of iam cache lookup ghost cleaner. |
| iam_cache_lookup_index_page_manager_count | long | Number of iam cache lookup index page manager. |
| iam_cache_lookup_shrink_count | long | Number of iam cache lookup shrink. |
| iam_cache_lookup_update_or_insert_checks_count | long | Number of iam cache lookup update or insert checks. |
| iam_page_range_cache_actual_invalidations_count | long | Number of iam page range cache actual invalidations. |
| iam_page_range_cache_addition_count | long | Number of iam page range cache addition. |
| iam_page_range_cache_invalidations_count | long | Number of iam page range cache invalidations. |
| iam_page_range_cache_populate_chainlength_max | long | Iam page range cache populate chainlength max. |
| iam_page_range_cache_populate_duration_us_max | long | Iam page range cache populate duration us max. |
| iam_page_range_cache_populate_fail_chainlength_sum | long | Iam page range cache populate fail chainlength sum. |
| iam_page_range_cache_populate_fail_count | long | Number of iam page range cache populate fail. |
| iam_page_range_cache_populate_fail_duration_sum_us | long | Iam page range cache populate fail duration sum us. |
| iam_page_range_cache_populate_lock_not_acquired_count | long | Number of iam page range cache populate lock not acquired. |
| iam_page_range_cache_populate_success_chainlength_sum | long | Iam page range cache populate success chainlength sum. |
| iam_page_range_cache_populate_success_count | long | Number of iam page range cache populate success. |
| iam_page_range_cache_populate_success_duration_sum_us | long | Iam page range cache populate success duration sum us. |
| in_row_non_data_pages_swept | long | In row non data pages swept. |
| in_row_non_data_pages_swept_percent | long | In row non data pages swept percentage. |
| in_row_pages_swept | long | In row pages swept. |
| in_row_pages_swept_marked_no_versions | long | In row pages swept marked no versions. |
| in_row_version_cleaner_end_time | datetime | In row version cleaner end time timestamp. |
| in_row_version_cleaner_start_time | datetime | In row version cleaner start time timestamp. |
| index_depth | long | Index depth. |
| index_id | long | Index identifier. |
| index_type_desc | long | Index type desc. |
| inpage_record_read_count | long | Number of inpage record read. |
| inrow_diff_skipped_count_same_xdes | long | Inrow diff skipped count same xdes. |
| inrow_diff_skipped_same_xdes_count | long | Number of inrow diff skipped same xdes. |
| inrow_diff_version_count | long | Number of inrow diff version. |
| inrow_diff_version_too_large_count | long | Number of inrow diff version too large. |
| inrow_full_version_count | long | Number of inrow full version. |
| inrow_full_version_too_large_count | long | Number of inrow full version too large. |
| inrow_ghost_pushed_off_row_count | long | Number of inrow ghost pushed off row. |
| inrow_ghost_version_count | long | Number of inrow ghost version. |
| inrow_pages_cold_read | long | Inrow pages cold read. |
| inrow_pages_io_wait_time | long | Inrow pages I/O wait time timestamp. |
| inrow_pages_reads_in_progress | long | Inrow pages reads in progress. |
| inrow_pushed_off_row_count | long | Number of inrow pushed off row. |
| inrow_skip_compressed_pages | long | Inrow skip compressed pages. |
| inrow_skip_compressed_pages_count | long | Number of inrow skip compressed pages. |
| inrow_skip_forwarded_record | long | Inrow skip forwarded record. |
| inrow_skip_forwarded_record_count | long | Number of inrow skip forwarded record. |
| inrow_skip_in_place_update_ctxt | long | Inrow skip in place update ctxt. |
| inrow_skip_in_place_update_ctxt_count | long | Number of inrow skip in place update ctxt. |
| inrow_skip_no_space_ghosting | long | Inrow skip no space ghosting. |
| inrow_skip_no_space_ghosting_count | long | Number of inrow skip no space ghosting. |
| inrow_skip_no_space_vrp | long | Inrow skip no space vrp. |
| inrow_skip_no_space_vrp_count | long | Number of inrow skip no space vrp. |
| inrow_skip_not_hobt_data_page | long | Inrow skip not hobt data page. |
| inrow_skip_not_hobt_data_page_count | long | Number of inrow skip not hobt data page. |
| inrow_skip_sequence | long | Inrow skip sequence. |
| inrow_skip_sequence_count | long | Number of inrow skip sequence. |
| inrow_skip_ts_interesting | long | Inrow skip ts interesting. |
| inrow_skip_ts_interesting_count | long | Number of inrow skip ts interesting. |
| inserts_in_ddl_transaction | long | Inserts in ddl transaction. |
| invalidation_reason | string | Invalidation reason. |
| is_accept_log_mode | bool | Boolean flag indicating whether accept log mode. |
| is_acceptlog_mode | bool | Boolean flag indicating whether acceptlog mode. |
| is_adr_disabled_by_design | bool | Boolean flag indicating whether adr disabled by design. |
| is_adr_disabled_by_traceflag | bool | Boolean flag indicating whether adr disabled by traceflag. |
| is_adr_enabled | bool | Boolean flag indicating whether adr enabled. |
| is_cleanup_under_user_transaction_enabled | bool | Boolean flag indicating whether cleanup under user transaction enabled. |
| is_concurrent_gam_enabled | long | Boolean flag indicating whether concurrent gam enabled. |
| is_concurrent_pfs_enabled | long | Boolean flag indicating whether concurrent pfs enabled. |
| is_concurrent_sgam_enabled | bool | Boolean flag indicating whether concurrent sgam enabled. |
| is_ctr_enabled | bool | Boolean flag indicating whether ctr enabled. |
| is_current_sweep_parallelized_within_database | bool | Boolean flag indicating whether current sweep parallelized within database. |
| is_elastic_pool_db | long | Boolean flag indicating whether elastic pool database. |
| is_log_accept_mode | bool | Boolean flag indicating whether log accept mode. |
| is_logical_revert_needed | bool | Boolean flag indicating whether logical revert needed. |
| is_long_term_pvs | bool | Boolean flag indicating whether long term pvs. |
| is_mtvc_enabled | long | Boolean flag indicating whether mtvc enabled. |
| is_mtvc_within_db_enabled | long | Boolean flag indicating whether mtvc within database enabled. |
| is_nest_id_hp_db_scoped_config_enabled | bool | Boolean flag indicating whether nest id hp database scoped config enabled. |
| is_nest_id_hp_enabled | bool | Boolean flag indicating whether nest id hp enabled. |
| is_persisted_version_enabled | bool | Boolean flag indicating whether persisted version enabled. |
| is_pvs_enabled | bool | Boolean flag indicating whether pvs enabled. |
| lock_resource_ids_added_to_hash_table | long | Lock resource ids added to hash table. |
| lock_resource_ids_removed_from_hash_table | long | Lock resource ids removed from hash table. |
| logical_database_guid | string | Logical database guid. |
| long_term_pvs_free_pages_kb | long | Long term pvs free pages kb. |
| long_term_pvs_off_row_inserts | long | Long term pvs off row inserts. |
| long_term_pvs_size_kb | long | Long term pvs size kb. |
| long_term_version_store_free_pages_kb | long | Long term version store free pages kb. |
| long_term_version_store_kb | long | Long term version store kb. |
| long_tx_rollback_count | long | Number of long tx rollback. |
| low_watermark_xdes_id_high | long | Low watermark xdes id high. |
| low_watermark_xdes_id_low | long | Low watermark xdes id low. |
| lr_blob_count | long | Number of lr blob. |
| lr_btree_count | long | Number of lr btree. |
| lr_heap_count | long | Number of lr heap. |
| max_version_chain_lr | long | Maximum version chain lr. |
| max_version_chain_query | long | Maximum version chain query. |
| max_version_chain_query_number_versions_traversed | long | Maximum version chain query number versions traversed. |
| max_version_chain_query_time_traversed_ms | long | Maximum version chain query time traversed ms. |
| min_active_xts | long | Minimum active xts. |
| min_useful_xts | long | Minimum useful xts. |
| min_useful_xts_regular | long | Minimum useful xts regular. |
| min_xdes_ts_in_move_page_after_recalculation | long | Minimum xdes ts in move page after recalculation. |
| min_xdes_ts_in_move_page_before_recalculation | long | Minimum xdes ts in move page before recalculation. |
| minimum_num_extents_per_iteration | long | Minimum num extents per iteration. |
| moved_version_pages_needing_reclean | long | Moved version pages needing reclean. |
| moved_version_pages_recleaned | long | Moved version pages recleaned. |
| multiple_version_from_nest_tran | long | Multiple version from nest tran. |
| nest_aborted_count | long | Number of nest aborted. |
| nest_id_from_off_row_count | long | Number of nest id from off row. |
| no_rlq_bit_cleared_left_page | long | No rlq bit cleared left page. |
| no_rlq_bit_cleared_right_page | long | No rlq bit cleared right page. |
| non_valid_slots | long | Non valid slots. |
| num_free_pvs_pages_available | long | Num free pvs pages available. |
| num_preallocation_iterations | long | Num preallocation iterations. |
| number_of_worker_migrations | long | Number of worker migrations. |
| object_id | long | Object identifier. |
| off_row_version_for_blob_deletes_count | long | Number of off row version for blob deletes. |
| off_row_version_for_blob_inserts_count | long | Number of off row version for blob inserts. |
| off_row_version_for_blob_updates_count | long | Number of off row version for blob updates. |
| off_row_version_for_delete_count | long | Number of off row version for delete. |
| off_row_version_for_lob_count | long | Number of off row version for lob. |
| off_row_version_ptr_reused_count | long | Number of off row version ptr reused. |
| oldest_abort_xdes_id_high | long | Oldest abort xdes id high. |
| oldest_abort_xdes_id_low | long | Oldest abort xdes id low. |
| oldest_active_xdes_id_high | long | Oldest active xdes id high. |
| oldest_active_xdes_id_low | long | Oldest active xdes id low. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| page_count | long | Number of page. |
| page_discards_for_PFS_pages | long | Page discards for PFS pages. |
| page_discards_for_data_pages | long | Page discards for data pages. |
| page_skipped_shrink_lock_failed | long | Page skipped shrink lock failed. |
| page_splits_for_delete | long | Page splits for delete. |
| page_splits_for_empty_btree | long | Page splits for empty btree. |
| page_splits_for_ghost | long | Page splits for ghost. |
| page_splits_for_insert | long | Page splits for insert. |
| page_splits_for_internal_node | long | Page splits for internal node. |
| page_splits_for_new_page | long | Page splits for new page. |
| page_splits_for_revert | long | Page splits for revert. |
| page_splits_for_root_node | long | Page splits for root node. |
| page_splits_for_update | long | Page splits for update. |
| pagesEmptyAfterClean | long | Pages Empty After Clean. |
| pagesEmptyNotRemovedChangedInBtree | long | Pages Empty Not Removed Changed In Btree. |
| pagesEmptyNotRemovedLastGhostNotRemovable | long | Pages Empty Not Removed Last Ghost Not Removable. |
| pagesEmptyNotRemovedLocks | long | Pages Empty Not Removed Locks. |
| pagesEmptyNotRemovedTopOfBtree | long | Pages Empty Not Removed Top Of Btree. |
| pagesEmptyRemovedAfterClean | long | Pages Empty Removed After Clean. |
| pagesEmptyRemovedTotal | long | Pages Empty Removed Total. |
| pagesProcessed | long | Pages Processed. |
| pagesSkippedChangedInBtree | long | Pages Skipped Changed In Btree. |
| pagesSkippedLastGhostNotRemovable | long | Pages Skipped Last Ghost Not Removable. |
| pagesSkippedLocks | long | Pages Skipped Locks. |
| pagesSkippedNoGhostRecords | long | Pages Skipped No Ghost Records. |
| pagesSkippedNotPartOfHobt | long | Pages Skipped Not Part Of Hobt. |
| pagesSkippedSlotInvalid | long | Pages Skipped Slot Invalid. |
| pagesSkippedTopOfBtree | long | Pages Skipped Top Of Btree. |
| pagesSkippedUnknown | long | Pages Skipped Unknown. |
| pages_added_to_hash_table | long | Pages added to hash table. |
| pages_cleaned_up_by_user_transactions | long | Pages cleaned up by user transactions. |
| pages_deallocated_compaction | long | Pages deallocated compaction. |
| pages_deallocated_ghost_cleanup | long | Pages deallocated ghost cleanup. |
| pages_needing_additional_cleanup | long | Pages needing additional cleanup. |
| pages_removed_from_hash_table_by_user_transactions | long | Pages removed from hash table by user transactions. |
| pages_removed_from_hash_table_by_version_cleaner | long | Pages removed from hash table by version cleaner. |
| pages_skipped_by_user_transactions | long | Pages skipped by user transactions. |
| parent_xdes_id_high | long | Parent xdes id high. |
| parent_xdes_id_low | long | Parent xdes id low. |
| parent_xdes_transactionName | string | Parent xdes transaction Name. |
| partition_number | long | Partition number. |
| persisted_version_store_free_pages_kb | long | Persisted version store free pages kb. |
| persisted_version_store_kb | long | Persisted version store kb. |
| pfs_concurrent_update_count | long | Number of pfs concurrent update. |
| pfs_exclusive_update_count | long | Number of pfs exclusive update. |
| pfs_exclusive_update_free_space_change_count | long | Number of pfs exclusive update free space change. |
| pfs_exclusive_update_tx_rollback_count | long | Number of pfs exclusive update tx rollback. |
| physical_db_id | string | Physical database identifier. |
| prev_adr_sweep_time | long | Prev adr sweep time timestamp. |
| prev_ctr_sweep_time | long | Prev ctr sweep time timestamp. |
| pvs_off_row_inserts | long | Pvs off row inserts. |
| pvs_off_row_long_term_inserts | long | Pvs off row long term inserts. |
| pvs_off_row_page_skipped_low_water_mark | long | Pvs off row page skipped low water mark. |
| pvs_off_row_page_skipped_min_useful_xts | long | Pvs off row page skipped min useful xts. |
| pvs_off_row_page_skipped_oldest_aborted_xdesid | long | Pvs off row page skipped oldest aborted xdesid. |
| pvs_off_row_page_skipped_oldest_active_xdesid | long | Pvs off row page skipped oldest active xdesid. |
| pvs_off_row_page_skipped_oldest_snapshot | long | Pvs off row page skipped oldest snapshot. |
| pvs_off_row_page_skipped_transaction_not_cleaned | long | Pvs off row page skipped transaction not cleaned. |
| pvs_off_row_pages_not_eligible_for_cleanup | long | Pvs off row pages not eligible for cleanup. |
| pvs_off_row_version_cleaner_end_time | datetime | Pvs off row version cleaner end time timestamp. |
| pvs_off_row_version_cleaner_start_time | datetime | Pvs off row version cleaner start time timestamp. |
| recordsCleaned | long | Records Cleaned. |
| recordsSkippedAfterOldestSnapshot | long | Records Skipped After Oldest Snapshot. |
| recordsSkippedDam | long | Records Skipped Dam. |
| recordsSkippedEntirePageSkipped | long | Records Skipped Entire Page Skipped. |
| recordsSkippedLocks | long | Records Skipped Locks. |
| recordsSkippedLowWatermark | long | Records Skipped Low Watermark. |
| recordsSkippedMinUsefulXts | long | Records Skipped Min Useful Xts. |
| recordsSkippedPageNotAllocated | long | Records Skipped Page Not Allocated. |
| recordsSkippedUnknown | long | Records Skipped Unknown. |
| recordsTotal | long | Records Total. |
| regular_pvs_free_pages_kb | long | Regular pvs free pages kb. |
| regular_pvs_size_kb | long | Regular pvs size kb. |
| row_count | long | Number of row. |
| rows_moved | long | Rows moved. |
| sampled_page_count | long | Number of sampled page. |
| savepoint_aborted_count | long | Number of savepoint aborted. |
| scan_all_pages | bool | Boolean flag indicating whether scan all pages. |
| scan_mode | long | Scan mode. |
| sessionName | string | Session Name. |
| sgam_concurrent_update_count | long | Number of sgam concurrent update. |
| sgam_exclusive_update_count | long | Number of sgam exclusive update. |
| short_tx_rollback_count | long | Number of short tx rollback. |
| shrink_data_file_count | long | Number of shrink data file. |
| snapshot_lock_resource_ids_in_hash_table | long | Snapshot lock resource ids in hash table. |
| snapshot_pages_in_hash_table | long | Snapshot pages in hash table. |
| stale_version_bytes_attempt | long | Stale version size in bytes attempt. |
| stale_version_cleanup_attempt | long | Stale version cleanup attempt. |
| stale_version_pages_cleaned | long | Stale version pages cleaned. |
| stale_version_purged_rows | long | Stale version purged rows. |
| stale_version_stripped_rows | long | Stale version stripped rows. |
| stale_version_unghosted_rows | long | Stale version unghosted rows. |
| status | string | Current status reported by the component. |
| suspend_count | long | Number of suspend. |
| suspend_io_count | long | Number of suspend I/O. |
| suspend_time_ms | long | Suspend time ms in milliseconds. |
| sweep_succeeded | bool | Boolean flag indicating whether sweep succeeded. |
| task_name | string | Task name. |
| tempdb_version_store_inserts | long | Tempdb version store inserts. |
| tempdb_version_store_small_inserts | long | Tempdb version store small inserts. |
| total_pvs_page_requests | long | Total pvs page requests. |
| total_size_of_changed_data_after_update | long | Total size of changed data after update. |
| total_size_of_rows_before_update | long | Total size of rows before update. |
| total_tx_count | long | Number of total tx. |
| tx_commit_count | long | Number of tx commit. |
| tx_explicit_count | long | Number of tx explicit. |
| tx_non_adr_count | long | Number of tx non adr. |
| tx_non_ctr_count | long | Number of tx non ctr. |
| tx_readcommitted_count | long | Number of tx readcommitted. |
| tx_readcommittedsnapshot_count | long | Number of tx readcommittedsnapshot. |
| tx_readuncommitted_count | long | Number of tx readuncommitted. |
| tx_repeatable_read_isolation | long | Tx repeatable read isolation. |
| tx_repeatableread_count | long | Number of tx repeatableread. |
| tx_rollback_count | long | Number of tx rollback. |
| tx_serializable_count | long | Number of tx serializable. |
| tx_serializable_isolation | long | Tx serializable isolation. |
| tx_snapshot_count | long | Number of tx snapshot. |
| tx_started_long_time_ago | long | Tx started long time ago. |
| tx_total_count | long | Number of tx total. |
| unique_transactions_attempting_page_cleanup | long | Unique transactions attempting page cleanup. |
| update_latch_pfs_free_space_change_count | long | Number of update latch pfs free space change. |
| update_latch_pfs_tx_rollback_count | long | Number of update latch pfs tx rollback. |
| updates_on_top_aborted_rows_count | long | Number of updates on top aborted rows. |
| version_ghost_record_count | long | Number of version ghost record. |
| version_page_record_read_count | long | Number of version page record read. |
| version_store_deep_reads | long | Version store deep reads. |
| version_store_diff_too_large | long | Version store diff too large. |
| version_store_inrow_diff | long | Version store inrow diff. |
| version_store_inrow_full | long | Version store inrow full. |
| version_store_inrow_ghost | long | Version store inrow ghost. |
| version_store_inrow_ghost_pushed_off | long | Version store inrow ghost pushed off. |
| version_store_inrow_pushed_off | long | Version store inrow pushed off. |
| version_store_offrow_for_delete | long | Version store offrow for delete. |
| version_store_offrow_for_lob | long | Version store offrow for lob. |
| version_store_pointer_reused | long | Version store pointer reused. |
| version_store_reads | long | Version store reads. |
| version_store_row_too_large | long | Version store row too large. |
| xdes_KBOfCurrentLogSpaceUsed | long | Xdes KBOf Current Log Space Used. |
| xdes_KBOfLogBetweenBeginLsnAndFirstReplLsn | long | Xdes KBOf Log Between Begin Lsn And First Repl Lsn. |
| xdes_KBOfLogUsedByTransaction | long | Xdes KBOf Log Used By Transaction. |
| xdes_KBOfLogUsedSinceBeginLsn | long | Xdes KBOf Log Used Since Begin Lsn. |
| xdes_beginLsn | string | Xdes begin Lsn. |
| xdes_beginTimestamp | string | Xdes begin timestamp. |
| xdes_exception_list_count | long | Number of xdes exception list. |
| xdes_exception_list_count_max | long | Xdes exception list count max. |
| xdes_firstReplLsn | string | Xdes first Repl Lsn. |
| xdes_id_high | long | Xdes id high. |
| xdes_id_low | long | Xdes id low. |
| xdes_is_aborted | bool | Boolean flag indicating whether xdes aborted. |
| xdes_lastLsn | string | Xdes last Lsn. |
| xdes_logRecCount | long | Xdes log Rec Count. |
| xdes_sessionId | long | Xdes session Id. |
| xdes_transactionId | long | Xdes transaction Id. |
| xdes_transactionName | string | Xdes transaction Name. |

## MonWiQdsExecStats — Query Store execution statistics

**Purpose**: Query Store execution statistics. Used to investigate slow queries, waits, blocking, deadlocks, and Query Store behavior. Referenced in MI template areas: backup-restore, performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| ResourcePoolName | string | Resource Pool Name. |
| clr_time | long | Clr time timestamp. |
| cpu_time | long | CPU time timestamp. |
| database_name | string | Database name. |
| dispatcher_plan_id | long | Dispatcher plan identifier. |
| distributed_request_id | string | Distributed request identifier. |
| distributed_step_index | string | Distributed step index. |
| dop | long | Dop. |
| elapsed_time | long | Elapsed duration for the operation. |
| event | string | Event name emitted by the component. |
| exec_type | long | Type classification for exec. |
| execution_count | long | Number of execution. |
| exhaust_epoch | long | Exhaust epoch. |
| first_exec_time_date | long | First exec time date. |
| first_exec_time_offset | long | First exec time offset. |
| first_exec_time_scale | long | First exec time scale. |
| first_exec_time_time_ms | long | First exec time time ms in milliseconds. |
| forced_plan_id | long | Forced plan identifier. |
| interval_end_time | long | Interval end time timestamp. |
| interval_id | long | Interval identifier. |
| interval_start_time | long | Interval start time timestamp. |
| is_parameterizable | bool | Boolean flag indicating whether parameterizable. |
| is_primary | bool | Boolean flag indicating whether primary. |
| last_exec_time_date | long | Last exec time date. |
| last_exec_time_offset | long | Last exec time offset. |
| last_exec_time_scale | long | Last exec time scale. |
| last_exec_time_time_ms | long | Last exec time time ms in milliseconds. |
| log_bytes_used | long | Log size in bytes used. |
| logical_database_guid | string | Logical database guid. |
| logical_reads | long | Logical reads. |
| logical_writes | long | Logical writes. |
| max_clr_time | long | Max clr time timestamp. |
| max_cpu_time | long | Max CPU time timestamp. |
| max_dop | long | Maximum dop. |
| max_elapsed_time | long | Max elapsed time timestamp. |
| max_log_bytes_used | long | Maximum log size in bytes used. |
| max_logical_reads | long | Maximum logical reads. |
| max_logical_writes | long | Maximum logical writes. |
| max_max_query_memory_pages | long | Maximum max query memory pages. |
| max_num_physical_io_reads | long | Maximum num physical I/O reads. |
| max_page_server_reads | long | Maximum page server reads. |
| max_physical_reads | long | Maximum physical reads. |
| max_query_memory_pages | long | Maximum query memory pages. |
| max_rowcount | long | Maximum rowcount. |
| max_tempdb_space_used | long | Maximum tempdb space used. |
| min_clr_time | long | Min clr time timestamp. |
| min_cpu_time | long | Min CPU time timestamp. |
| min_dop | long | Minimum dop. |
| min_elapsed_time | long | Min elapsed time timestamp. |
| min_log_bytes_used | long | Minimum log size in bytes used. |
| min_logical_reads | long | Minimum logical reads. |
| min_logical_writes | long | Minimum logical writes. |
| min_max_query_memory_pages | long | Minimum max query memory pages. |
| min_num_physical_io_reads | long | Minimum num physical I/O reads. |
| min_page_server_reads | long | Minimum page server reads. |
| min_physical_reads | long | Minimum physical reads. |
| min_rowcount | long | Minimum rowcount. |
| min_tempdb_space_used | long | Minimum tempdb space used. |
| num_physical_io_reads | long | Num physical I/O reads. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| page_server_reads | long | Page server reads. |
| parent_query_id | long | Parent query identifier. |
| physical_reads | long | Physical reads. |
| plan_forcing_type | string | Type classification for plan forcing. |
| plan_id | long | Plan identifier. |
| query_hash | string | Query hash. |
| query_id | long | Query identifier. |
| query_param_type | long | Type classification for query param. |
| query_plan_hash | string | Query plan hash. |
| replica_group_id | long | Replica group identifier. |
| rowcount | long | Rowcount. |
| runtime_stats_exhaust_type | string | Type classification for runtime stats exhaust. |
| server_name | string | Managed Instance server name. |
| sessionName | string | Session Name. |
| statement_key_hash | long | Statement key hash. |
| statement_sql_hash | string | Statement SQL hash. |
| statement_type | string | Type classification for statement. |
| sum_squares_clr_time | real | Sum squares clr time timestamp. |
| sum_squares_cpu_time | real | Sum squares CPU time timestamp. |
| sum_squares_dop | real | Sum squares dop. |
| sum_squares_elapsed_time | real | Sum squares elapsed time timestamp. |
| sum_squares_log_bytes_used | real | Sum squares log size in bytes used. |
| sum_squares_logical_reads | real | Sum squares logical reads. |
| sum_squares_logical_writes | real | Sum squares logical writes. |
| sum_squares_max_query_memory_pages | real | Sum squares max query memory pages. |
| sum_squares_num_physical_io_reads | real | Sum squares num physical I/O reads. |
| sum_squares_page_server_reads | real | Sum squares page server reads. |
| sum_squares_physical_reads | real | Sum squares physical reads. |
| sum_squares_rowcount | real | Sum squares rowcount. |
| sum_squares_tempdb_space_used | real | Sum squares tempdb space used. |
| tempdb_space_used | long | Tempdb space used. |
| template_hash | string | Template hash. |
| update_id | long | Update identifier. |

## MonWiQdsWaitStats — Query Store wait statistics

**Purpose**: Query Store wait statistics. Used to investigate slow queries, waits, blocking, deadlocks, and Query Store behavior. Referenced in MI template areas: performance. Often used to explain wait or latency patterns.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| ResourcePoolName | string | Resource Pool Name. |
| avg_query_wait_time_ms | real | Average query wait time ms. |
| database_name | string | Database name. |
| distributed_request_id | string | Distributed request identifier. |
| distributed_step_index | string | Distributed step index. |
| event | string | Event name emitted by the component. |
| exec_type | long | Type classification for exec. |
| interval_end_time | long | Interval end time timestamp. |
| interval_id | long | Interval identifier. |
| interval_start_time | long | Interval start time timestamp. |
| is_parameterizable | bool | Boolean flag indicating whether parameterizable. |
| is_primary | bool | Boolean flag indicating whether primary. |
| logical_database_guid | string | Logical database guid. |
| max_query_wait_time_ms | long | Maximum query wait time ms. |
| min_query_wait_time_ms | long | Minimum query wait time ms. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| plan_id | long | Plan identifier. |
| query_hash | string | Query hash. |
| query_id | long | Query identifier. |
| query_param_type | long | Type classification for query param. |
| query_plan_hash | string | Query plan hash. |
| replica_group_id | long | Replica group identifier. |
| runtime_stats_exhaust_type | string | Type classification for runtime stats exhaust. |
| server_name | string | Managed Instance server name. |
| sessionName | string | Session Name. |
| statement_key_hash | long | Statement key hash. |
| statement_sql_hash | string | Statement SQL hash. |
| statement_type | string | Type classification for statement. |
| sum_squares_query_wait_time_ms | real | Sum squares query wait time ms in milliseconds. |
| template_hash | string | Template hash. |
| total_query_wait_time_ms | long | Total query wait time ms. |
| wait_category | string | Wait category. |

## MonWiQueryParamData — Workload insights Query Param Data

**Purpose**: Workload insights Query Param Data. Used to investigate slow queries, waits, blocking, deadlocks, and Query Store behavior. Referenced in MI template areas: performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| auto_create_stats_cpu_time | long | Auto create stats CPU time timestamp. |
| auto_create_stats_elapsed_time | long | Auto create stats elapsed time timestamp. |
| auto_update_stats_cpu_time | long | Auto update stats CPU time timestamp. |
| auto_update_stats_elapsed_time | long | Auto update stats elapsed time timestamp. |
| cached_plan_size | long | Cached plan size. |
| compile_code | string | Compile code. |
| compile_cpu_time | long | Compile CPU time timestamp. |
| compile_duration | long | Compile duration. |
| compile_memory | long | Compile memory. |
| database_id | long | Database identifier. |
| distributed_execution_id | string | Distributed execution identifier. |
| distributed_query_hash | string | Distributed query hash. |
| distributed_query_operator_id | string | Distributed query operator identifier. |
| distributed_request_id | string | Distributed request identifier. |
| distributed_scheduler_id | string | Distributed scheduler identifier. |
| distributed_statement_id | string | Distributed statement identifier. |
| distributed_step_index | string | Distributed step index. |
| distributed_submission_id | string | Distributed submission identifier. |
| distributed_task_group_id | string | Distributed task group identifier. |
| event | string | Event name emitted by the component. |
| has_external_extraction | bool | Boolean flag indicating whether has external extraction. |
| has_literals | bool | Boolean flag indicating whether has literals. |
| ipcprocnum | long | Ipcprocnum. |
| is_cached | bool | Boolean flag indicating whether cached. |
| is_forced | bool | Boolean flag indicating whether forced. |
| is_parameterizable | bool | Boolean flag indicating whether parameterizable. |
| is_pch_query | bool | Boolean flag indicating whether pch query. |
| is_query_variant | bool | Boolean flag indicating whether query variant. |
| is_recompiled | string | Boolean flag indicating whether recompiled. |
| is_rpcrequest | bool | Boolean flag indicating whether rpcrequest. |
| logical_database_guid | string | Logical database guid. |
| logical_database_name | string | Logical database name. |
| mgf_persistence_used_status | string | Status value for mgf persistence used. |
| object_id | long | Object identifier. |
| optimization_cpu_time | long | Optimization CPU time timestamp. |
| optimization_duration | long | Optimization duration. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| parameterized_values_count | long | Number of parameterized values. |
| plan_Handle | string | Plan Handle. |
| query_adhoc_ce_feedback_iteration_number | long | Query adhoc ce feedback iteration number. |
| query_hash | string | Query hash. |
| query_param_type | long | Type classification for query param. |
| query_plan_hash | string | Query plan hash. |
| replay_mode | string | Replay mode. |
| sessionName | string | Session Name. |
| sql_Handle | string | SQL Handle. |
| statement_sql_hash | string | Statement SQL hash. |
| template_hash | string | Template hash. |
| uses_query_adhoc_ce_feedback | bool | Boolean flag indicating whether uses query adhoc ce feedback. |

# 7. Error & Health

## AlrMetricsForLogsToMetricsV1 — Metrics For Logs To Metrics V1

**Purpose**: Metrics For Logs To Metrics V1. Used to troubleshoot alerts, health transitions, dumps, crashes, and platform error signals. Referenced in MI template areas: networking.
**Category**: Monitoring

| Column | Type | Description |
|--------|------|-------------|
| OneBoxClusterId | string | One Box Cluster Id. |
| countValue | long | Number of count Value. |
| dimensionNameList | string | Dimension Name List. |
| dimensionValueList | string | Dimension Value List. |
| env_appId | string | Env app Id. |
| env_appVer | string | Env app Ver. |
| env_cloud_deploymentUnit | string | Env cloud deployment Unit. |
| env_cloud_environment | string | Env cloud environment. |
| env_cloud_location | string | Env cloud location. |
| env_cloud_name | string | Env cloud name. |
| env_cloud_role | string | Env cloud role. |
| env_cloud_roleInstance | string | Env cloud role Instance. |
| env_cloud_roleVer | string | Env cloud role Ver. |
| env_cloud_ver | string | Env cloud ver. |
| env_cv | string | Env correlation vector. |
| env_flags | long | Env flags. |
| env_iKey | string | Env i Key. |
| env_name | string | Env name. |
| env_seqNum | long | Env seq Num. |
| env_time | datetime | Env time timestamp. |
| env_ver | string | Env ver. |
| maxValue | long | Max Value. |
| metricName | string | Metric Name. |
| metricNamespace | string | Metric Namespace. |
| minValue | long | Min Value. |
| monitoringAccount | string | Monitoring Account. |
| samplingTypeFlags | long | Sampling Type Flags. |
| scalingFactor | float | Scaling Factor. |
| sumOfSquaresValue | float | Sum Of Squares Value. |
| sumValue | long | Sum Value. |
| timeBucketUtc | long | Time Bucket Utc. |

## AlrSharedMAHeartbeat — Shared MAHeartbeat

**Purpose**: Shared MAHeartbeat. Used to troubleshoot alerts, health transitions, dumps, crashes, and platform error signals. Referenced in MI template areas: backup-restore. Often used during backup or restore investigations.
**Category**: Monitoring

| Column | Type | Description |
|--------|------|-------------|
| MaVersion | string | Ma Version. |
| NodeMDSAgentSvc | string | Node MDSAgent Svc. |
| OneBoxClusterId | string | One Box Cluster Id. |
| PartitionId | string | Partition Id. |
| Pid | long | Pid. |
| Tid | long | Tid. |

## AlrSQLErrorsReported — SQL error reports and alert surface

**Purpose**: SQL error reports and alert surface. Used to troubleshoot alerts, health transitions, dumps, crashes, and platform error signals. Referenced in MI template areas: availability, backup-restore, performance.
**Category**: Monitoring

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| call_stack | string | Call stack. |
| callstack | string | Callstack. |
| callstack_rva | string | Callstack rva. |
| category | string | Category. |
| code_package_version | string | Code package version. |
| compile_plan_guid | string | Compile plan guid. |
| database_id | long | Database identifier. |
| database_name | string | Database name. |
| destination | string | Destination. |
| distributed_statement_id | string | Distributed statement identifier. |
| error_number | long | SQL or platform error number. |
| event | string | Event name emitted by the component. |
| execution_plan_guid | string | Execution plan guid. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| id | long | identifier. |
| is_azure_connection | bool | Boolean flag indicating whether azure connection. |
| is_intercepted | bool | Boolean flag indicating whether intercepted. |
| origin | string | Origin. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| query_hash | long | Query hash. |
| query_plan_hash | long | Query plan hash. |
| sessionName | string | Session Name. |
| session_id | long | Session identifier. |
| session_resource_group_id | long | Session resource group identifier. |
| severity | long | Severity level associated with the event. |
| state | long | Current lifecycle or health state. |
| task_address | string | Task address. |
| timestamp_exception_ring_buffer_recorded | long | Timestamp exception ring buffer recorded. |
| timestamp_exception_ring_buffer_recorded_rva | long | Timestamp exception ring buffer recorded rva. |
| tsql_stack | string | Tsql stack. |
| user_defined | bool | Boolean flag indicating whether user defined. |

## AlrSqlSatelliteRunner — SQL Satellite Runner

**Purpose**: SQL Satellite Runner. Used to troubleshoot alerts, health transitions, dumps, crashes, and platform error signals. Referenced in MI template areas: backup-restore.
**Category**: Monitoring

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| code_package_version | string | Code package version. |
| component | string | Component. |
| event | string | Event name emitted by the component. |
| message_systemmetadata | string | Message systemmetadata. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| process_id | long | Process identifier. |
| sessionName | string | Session Name. |
| severity | string | Severity level associated with the event. |
| version | string | Version. |

## AlrWinFabHealthApplicationState — Win Fabric Health Application State

**Purpose**: Win Fabric Health Application State. Used to troubleshoot alerts, health transitions, dumps, crashes, and platform error signals. Referenced in MI template areas: availability, networking.
**Category**: Monitoring

| Column | Type | Description |
|--------|------|-------------|
| ApplicationName | string | Application Name. |
| ClusterEntityName | string | Cluster Entity Name. |
| HealthState | string | Health State. |
| OneBoxClusterId | string | One Box Cluster Id. |
| ReasonUnhealthy | string | Reason Unhealthy. |
| RowKey | string | Row Key. |
| Version | long | Version. |

## AlrWinFabHealthNodeEvent — Win Fabric Health Node Event

**Purpose**: Win Fabric Health Node Event. Used to troubleshoot alerts, health transitions, dumps, crashes, and platform error signals. Referenced in MI template areas: availability, networking.
**Category**: Monitoring

| Column | Type | Description |
|--------|------|-------------|
| ClusterEntityName | string | Cluster Entity Name. |
| Description | string | Description. |
| HealthState | string | Health State. |
| IsExpired | bool | Boolean flag indicating whether Is Expired. |
| NodeEntityName | string | Node Entity Name. |
| OneBoxClusterId | string | One Box Cluster Id. |
| Property | string | Property. |
| SourceId | string | Source Id. |
| Version | long | Version. |

## AlrWinFabHealthPartitionEvent — Win Fabric Health Partition Event

**Purpose**: Win Fabric Health Partition Event. Used to troubleshoot alerts, health transitions, dumps, crashes, and platform error signals. Referenced in MI template areas: availability, networking.
**Category**: Monitoring

| Column | Type | Description |
|--------|------|-------------|
| ApplicationName | string | Application Name. |
| ClusterEntityName | string | Cluster Entity Name. |
| Description | string | Description. |
| HealthState | string | Health State. |
| IsExpired | bool | Boolean flag indicating whether Is Expired. |
| OneBoxClusterId | string | One Box Cluster Id. |
| PartitionId | string | Partition Id. |
| Property | string | Property. |
| ServiceName | string | Service Name. |
| SourceId | string | Source Id. |
| Version | long | Version. |

## AlrWinFabHealthReplicaEvent — Win Fabric Health Replica Event

**Purpose**: Win Fabric Health Replica Event. Used to troubleshoot alerts, health transitions, dumps, crashes, and platform error signals. Referenced in MI template areas: availability.
**Category**: Monitoring

| Column | Type | Description |
|--------|------|-------------|
| ApplicationName | string | Application Name. |
| ClusterEntityName | string | Cluster Entity Name. |
| Description | string | Description. |
| HealthState | string | Health State. |
| IsExpired | bool | Boolean flag indicating whether Is Expired. |
| OneBoxClusterId | string | One Box Cluster Id. |
| PartitionId | string | Partition Id. |
| Property | string | Property. |
| ReplicaId | long | Replica Id. |
| ServiceName | string | Service Name. |
| SourceId | string | Source Id. |
| Version | long | Version. |

## AlrWinFabHealthServiceState — Win Fabric Health Service State

**Purpose**: Win Fabric Health Service State. Used to troubleshoot alerts, health transitions, dumps, crashes, and platform error signals. Referenced in MI template areas: availability.
**Category**: Monitoring

| Column | Type | Description |
|--------|------|-------------|
| ApplicationName | string | Application Name. |
| ClusterEntityName | string | Cluster Entity Name. |
| HealthState | string | Health State. |
| OneBoxClusterId | string | One Box Cluster Id. |
| ReasonUnhealthy | string | Reason Unhealthy. |
| ServiceName | string | Service Name. |
| Version | long | Version. |

## MonAppEventLogErrors — App Event Log Errors

**Purpose**: App Event Log Errors. Used to troubleshoot alerts, health transitions, dumps, crashes, and platform error signals. Referenced in MI template areas: performance.
**Category**: Monitoring

| Column | Type | Description |
|--------|------|-------------|
| EventDescription | string | Event Description. |
| EventID | string | Event ID. |
| Level | long | Level. |
| OneBoxClusterId | string | One Box Cluster Id. |
| ProviderName | string | Provider Name. |

## MonHyperVEvents — Hyper VEvents

**Purpose**: Hyper VEvents. Used to troubleshoot alerts, health transitions, dumps, crashes, and platform error signals. Referenced in MI template areas: availability.
**Category**: Monitoring

| Column | Type | Description |
|--------|------|-------------|
| ActivityId | string | Activity Id. |
| ChannelName | string | Channel Name. |
| EventId | long | Event Id. |
| EventMessage | string | Event Message. |
| KeywordMask | long | Keyword Mask. |
| KeywordName | string | Keyword Name. |
| Level | long | Level. |
| Message | string | Human-readable message text. |
| OneBoxClusterId | string | One Box Cluster Id. |
| OpcodeName | string | Opcode Name. |
| Pid | long | Pid. |
| ProviderGuid | string | Provider Guid. |
| ProviderName | string | Provider Name. |
| RelatedActivityId | string | Related Activity Id. |
| TaskName | string | Task Name. |
| Tid | long | Tid. |

## MonMachineLocalWatchdog — Machine Local Watchdog

**Purpose**: Machine Local Watchdog. Used to troubleshoot alerts, health transitions, dumps, crashes, and platform error signals. Referenced in MI template areas: networking.
**Category**: Monitoring

| Column | Type | Description |
|--------|------|-------------|
| Level | long | Level. |
| Name | string | Object or resource name. |
| OneBoxClusterId | string | One Box Cluster Id. |
| Pid | long | Pid. |
| Tid | long | Tid. |
| Timestamp | string | timestamp. |
| _name | string | Name. |
| body | string | Body. |
| code_package_version | string | Code package version. |
| component | string | Component. |
| event | string | Event name emitted by the component. |
| message_resourcename | string | Message resourcename. |
| message_systemmetadata | string | Message systemmetadata. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| process_id | long | Process identifier. |
| sessionName | string | Session Name. |
| severity | string | Severity level associated with the event. |
| severityNumber | long | Severity Number. |
| severityText | string | Severity Text. |
| version | string | Version. |

## MonNodeAgentEvents — Node Agent Events

**Purpose**: Node Agent Events. Used to troubleshoot alerts, health transitions, dumps, crashes, and platform error signals. Referenced in MI template areas: networking, performance.
**Category**: Monitoring

| Column | Type | Description |
|--------|------|-------------|
| Level | long | Level. |
| Name | string | Object or resource name. |
| OneBoxClusterId | string | One Box Cluster Id. |
| Pid | long | Pid. |
| Tid | long | Tid. |
| Timestamp | string | timestamp. |
| _name | string | Name. |
| action | string | Action. |
| action_name | string | Action name. |
| authentication_type | string | Type classification for authentication. |
| autotuning_request_description | string | Autotuning request description. |
| autotuning_request_type | string | Type classification for autotuning request. |
| body | string | Body. |
| caller_ip_address | string | Caller ip address. |
| certificate_name | string | Certificate name. |
| chosen_certificate_thumbprint | string | Chosen certificate thumbprint. |
| client_timestamp | datetime | Client timestamp. |
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| component | string | Component. |
| content_length | long | Content length. |
| correlation_request_id | string | Correlation request identifier. |
| count | long | Number of count. |
| database_max_size_bytes | long | Database max size size in bytes. |
| database_name | string | Database name. |
| elapsed_time | string | Elapsed duration for the operation. |
| elapsed_time_milliseconds | real | Elapsed duration in milliseconds. |
| elasped_time | string | Elasped time timestamp. |
| endpoint_address | string | Endpoint address. |
| endpoints | string | Endpoints. |
| event | string | Event name emitted by the component. |
| event_type | string | Type classification for event. |
| exception | string | Exception. |
| exception_message | string | Exception message. |
| exception_type | string | Type classification for exception. |
| expiry_date | datetime | Expiry date. |
| fabric_service_uri | string | Fabric service uri. |
| file_growth_mb | string | File growth mb. |
| file_max_size_mb | string | File max size mb. |
| file_name | string | File name. |
| file_type | string | Type classification for file. |
| identity_name | string | Identity name. |
| index_name | string | Index name. |
| index_request_description | string | Index request description. |
| index_request_type | string | Type classification for index request. |
| instance_name | string | Instance name. |
| invalid_certificate_thumbprint | string | Invalid certificate thumbprint. |
| is_ab_test | bool | Boolean flag indicating whether ab test. |
| is_anonymous | bool | Boolean flag indicating whether anonymous. |
| is_async | bool | Boolean flag indicating whether async. |
| is_authenticated | bool | Boolean flag indicating whether authenticated. |
| is_successful | bool | Boolean flag indicating whether successful. |
| is_valid | bool | Boolean flag indicating whether valid. |
| issuer | string | Issuer. |
| issuer_name | string | Issuer name. |
| level | string | Level. |
| listen_address | string | Listen address. |
| logical_database_name | string | Logical database name. |
| master_database_name | string | Master database name. |
| message | string | Human-readable message text. |
| message_systemmetadata | string | Message systemmetadata. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| physical_database_id | string | Physical database identifier. |
| port | long | Port. |
| process_id | long | Process identifier. |
| purpose | string | Purpose. |
| query_plan_hash | string | Query plan hash. |
| request_id | string | Request identifier used to correlate the operation. |
| request_url | string | Request url. |
| resource_pool_name | string | Resource pool name. |
| schema_name | string | Schema name. |
| service_instance_name | string | Service instance name. |
| service_name | string | Service name. |
| service_type | string | Type classification for service. |
| sessionName | string | Session Name. |
| severityNumber | long | Severity Number. |
| severityText | string | Severity Text. |
| stack_trace | string | Stack trace. |
| subject_name | string | Subject name. |
| substring_length | long | Substring length. |
| substring_start | long | Substring start. |
| table_name | string | Table name. |
| target_max_size_bytes | long | Target max size size in bytes. |
| tempdb_file_type | string | Type classification for tempdb file. |
| thumbprint | string | Thumbprint. |
| thumbprint2 | string | Thumbprint2. |
| thumbprints | string | Thumbprints. |
| trusted_sans | string | Trusted sans. |
| trusted_thumbprints | string | Trusted thumbprints. |
| user_agent | string | User agent. |
| verb | string | Verb. |

## MonNodeTraceETW — Node Trace ETW

**Purpose**: Node Trace ETW. Used to troubleshoot alerts, health transitions, dumps, crashes, and platform error signals. Referenced in MI template areas: availability, backup-restore, networking. Often used during backup or restore investigations.
**Category**: Monitoring

| Column | Type | Description |
|--------|------|-------------|
| ActivityId | string | Activity Id. |
| ChannelName | string | Channel Name. |
| ContainerId | string | Container Id. |
| EventId | long | Event Id. |
| EventMessage | string | Event Message. |
| KeywordName | string | Keyword Name. |
| Level | long | Level. |
| Message | string | Human-readable message text. |
| OneBoxClusterId | string | One Box Cluster Id. |
| OpcodeName | string | Opcode Name. |
| Pid | long | Pid. |
| ProviderGuid | string | Provider Guid. |
| ProviderName | string | Provider Name. |
| TaskName | string | Task Name. |
| Tid | long | Tid. |

## MonSqlBrokerRingBuffer — SQL Broker Ring Buffer

**Purpose**: SQL Broker Ring Buffer. Used to troubleshoot alerts, health transitions, dumps, crashes, and platform error signals. Referenced in MI template areas: performance.
**Category**: Monitoring

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| attach_activity_id | string | Attach activity identifier. |
| attach_activity_id_xfer | string | Attach activity id xfer. |
| broker | string | Broker. |
| call_stack | string | Call stack. |
| code_package_version | string | Code package version. |
| currently_allocated | long | Currently allocated. |
| currently_predicated | long | Currently predicated. |
| delta_time | long | Delta time timestamp. |
| event | string | Event name emitted by the component. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| id | long | identifier. |
| memory_ratio | long | Memory ratio. |
| new_target | long | New target. |
| notification | string | Notification. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| overall | long | Overall. |
| package | string | Package. |
| pool_metadata_id | long | Pool metadata identifier. |
| previously_allocated | long | Previously allocated. |
| process_id | long | Process identifier. |
| rate | long | Rate. |
| sessionName | string | Session Name. |
| system_thread_id | long | System thread identifier. |
| timestamp_memory_broker_ring_buffer_recorded | long | Timestamp memory broker ring buffer recorded. |

## MonSqlDump — SQL Dump

**Purpose**: SQL Dump. Used to troubleshoot alerts, health transitions, dumps, crashes, and platform error signals. Referenced in MI template areas: availability, backup-restore.
**Category**: Monitoring

| Column | Type | Description |
|--------|------|-------------|
| CompleteFileName | string | Complete File Name. |
| Container | string | Container. |
| ContextParam | string | Context Param. |
| FileSize | long | File Size. |
| FileTime | datetime | File Time. |
| RelativePath | string | Relative Path. |
| SourceDirectory | string | Source Directory. |

## MonSqlDumperActivity — SQL Dumper Activity

**Purpose**: SQL Dumper Activity. Used to troubleshoot alerts, health transitions, dumps, crashes, and platform error signals. Referenced in MI template areas: availability, backup-restore. Often used during backup or restore investigations.
**Category**: Monitoring

| Column | Type | Description |
|--------|------|-------------|
| AWDumpOutput | string | AWDump Output. |
| AWDumpProductVersion | string | AWDump Product Version. |
| ActivityId | string | Activity Id. |
| AddFileErrorCode | long | Add File Error Code. |
| BranchName | string | Branch Name. |
| BuildFlavor | string | Build Flavor. |
| CallStack | string | Call Stack. |
| ChannelName | string | Channel Name. |
| CommandLine | string | Command Line. |
| CompleteFileName | string | Complete File Name. |
| CompressionRate | long | Compression Rate. |
| ContainerId | string | Container Id. |
| DumpErrorDetails | string | Dump Error Details. |
| DumpErrorText | string | Dump Error Text. |
| DumpFlags | long | Dump Flags. |
| DumpUID | string | Dump UID. |
| DumperEndTime | datetime | Dumper End Time. |
| DumperProductVersion | string | Dumper Product Version. |
| DumperStartTime | datetime | Dumper Start Time. |
| ErrorCode | long | Error Code. |
| EventMessage | string | Event Message. |
| FailReason | string | Fail Reason. |
| FileSize | long | File Size. |
| FileTime | datetime | File Time. |
| IsDumpAvoided | bool | Boolean flag indicating whether Is Dump Avoided. |
| IsFailed | bool | Boolean flag indicating whether Is Failed. |
| IsSubmitFailed | bool | Boolean flag indicating whether Is Submit Failed. |
| IsWatsonInvoke | bool | Boolean flag indicating whether Is Watson Invoke. |
| KeywordName | string | Keyword Name. |
| Level | long | Level. |
| MDWDEndTime | datetime | MDWDEnd Time. |
| MDWDStartTime | datetime | MDWDStart Time. |
| MiniDumpType | long | Mini Dump Type. |
| MoreInfo | string | More Info. |
| OfficialBuild | string | Official Build. |
| OneBoxClusterId | string | One Box Cluster Id. |
| OpcodeName | string | Opcode Name. |
| Pid | long | Pid. |
| ProviderGuid | string | Provider Guid. |
| ProviderName | string | Provider Name. |
| QBuildGuid | string | QBuild Guid. |
| QBuildSyncChangeset | string | QBuild Sync Changeset. |
| SQLDumpType | long | SQLDump Type. |
| SQLMemoryModel | string | SQLMemory Model. |
| Shadow_Violation | string | Shadow Violation. |
| StackSignature | string | Stack Signature. |
| SubmitEndTime | datetime | Submit End Time. |
| SubmitErrorCode | long | Submit Error Code. |
| SubmitFailReason | string | Submit Fail Reason. |
| SubmitResult | long | Submit Result. |
| SubmitResultDesc | string | Submit Result Desc. |
| SubmitStartTime | datetime | Submit Start Time. |
| TargetAppName | string | Target app Name. |
| TargetAppTypeName | string | Target app Type Name. |
| TargetFullName | string | Target Full Name. |
| TargetLogicalServerName | string | Target Logical Server Name. |
| TargetPid | long | Target Pid. |
| TargetProcess | string | Target Process. |
| TargetProductVersion | string | Target Product Version. |
| TaskName | string | Task Name. |
| Tid | long | Tid. |

## MonSqlRmRingBuffer — SQL Rm Ring Buffer

**Purpose**: SQL Rm Ring Buffer. Used to troubleshoot alerts, health transitions, dumps, crashes, and platform error signals. Referenced in MI template areas: performance.
**Category**: Monitoring

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| apply_high_pm | string | Apply high pm. |
| apply_low_pm | string | Apply low pm. |
| attach_activity_id | string | Attach activity identifier. |
| attach_activity_id_xfer | string | Attach activity id xfer. |
| available_extended_virtual_address_space_kb | long | Available extended virtual address space kb. |
| available_memory_free_block_emergency_descriptors | long | Available memory free block emergency descriptors. |
| available_page_file_kb | long | Available page file kb. |
| available_physical_memory_kb | long | Available physical memory kb. |
| available_virtual_address_space_kb | long | Available virtual address space kb. |
| awe_kb | long | Awe kb. |
| azure_profiler_flavor | long | Azure profiler flavor. |
| call_stack | string | Call stack. |
| call_stack_rva | string | Call stack rva. |
| code_package_version | string | Code package version. |
| committed_kb | long | Committed kb. |
| database_id | long | Database identifier. |
| dispatcher_pool_name | string | Dispatcher pool name. |
| duration | long | Duration. |
| event | string | Event name emitted by the component. |
| event_handle | string | Event handle. |
| file_handle | string | File handle. |
| file_id | long | File identifier. |
| file_path | string | File path. |
| group_indicators | long | Group indicators. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| hresult | long | Hresult. |
| id | long | identifier. |
| instance_partition_id | string | Instance partition identifier. |
| instance_replica_id | long | Instance replica identifier. |
| is_process_in_job | bool | Boolean flag indicating whether process in job. |
| is_process_physical_memory_low | bool | Boolean flag indicating whether process physical memory low. |
| is_process_virtual_memory_low | bool | Boolean flag indicating whether process virtual memory low. |
| is_success | bool | Boolean flag indicating whether success. |
| is_system_physical_memory_high | bool | Boolean flag indicating whether system physical memory high. |
| is_system_physical_memory_low | bool | Boolean flag indicating whether system physical memory low. |
| job_object_limit_job_mem_kb | long | Job object limit job memory kb. |
| job_object_limit_process_mem_kb | long | Job object limit process memory kb. |
| kernel_mode_time | long | Kernel mode time timestamp. |
| kernel_mode_time_ms | long | Kernel mode time ms in milliseconds. |
| last_long_io_offset | long | Last long I/O offset. |
| logical_db_id | string | Logical database identifier. |
| longer_than_sec | long | Longer than sec. |
| memory_allocated | long | Memory allocated. |
| memory_node_id | long | Memory node identifier. |
| memory_released_in_rm_phase_kb | long | Memory released in rm phase kb. |
| memory_utilization | long | Memory utilization. |
| memory_utilization_pct | long | Memory utilization pct. |
| new_affinity_mask | long | New affinity mask. |
| node_id | long | Node identifier. |
| nonyield_type | long | Type classification for nonyield. |
| notification | string | Notification. |
| occurrences | long | Occurrences. |
| old_affinity_mask | long | Old affinity mask. |
| opcode | string | Opcode. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| page_faults | long | Page faults. |
| pages_kb | long | Pages kb. |
| peak_job_memory_used_kb | long | Peak job memory used kb. |
| peak_process_memory_used_kb | long | Peak process memory used kb. |
| physical_db_id | string | Physical database identifier. |
| pool_indicators | long | Pool indicators. |
| process_id | long | Process identifier. |
| process_indicators | long | Process indicators. |
| process_utilization | long | Process utilization. |
| reconfig_result | long | Reconfig result. |
| request_id | long | Request identifier used to correlate the operation. |
| reserved_kb | long | Reserved kb. |
| revert_high_pm | string | Revert high pm. |
| rm_memory_pressure_phase | string | Rm memory pressure phase. |
| scheduler | long | Scheduler. |
| scheduler_id | long | Scheduler identifier. |
| sessionName | string | Session Name. |
| session_id | long | Session identifier. |
| shared_committed_kb | long | Shared committed kb. |
| stack_frames | string | Stack frames. |
| system_idle | long | System idle. |
| system_indicators | long | System indicators. |
| system_thread | string | System thread. |
| system_thread_id | long | System thread identifier. |
| target_kb | long | Target kb. |
| task | string | Task. |
| thread_id | long | Thread identifier. |
| timestamp_nonyield_copiedstack_ring_buffer_recorded | long | Timestamp nonyield copiedstack ring buffer recorded. |
| timestamp_resource_monitor_ring_buffer_recorded | long | Timestamp resource monitor ring buffer recorded. |
| timestamp_scheduler_monitor_deadlock_ring_buffer_recorded | long | Timestamp scheduler monitor deadlock ring buffer recorded. |
| timestamp_scheduler_monitor_non_yielding_iocp_ring_buffer_recor | long | Timestamp scheduler monitor non yielding iocp ring buffer recor. |
| timestamp_scheduler_monitor_non_yielding_ring_buffer_recorded | long | Timestamp scheduler monitor non yielding ring buffer recorded. |
| timestamp_scheduler_monitor_non_yielding_rm_ring_buffer_recorde | long | Timestamp scheduler monitor non yielding rm ring buffer recorde. |
| timestamp_scheduler_monitor_stalled_dispatcher_ring_buffer_reco | long | Timestamp scheduler monitor stalled dispatcher ring buffer reco. |
| timestamp_scheduler_monitor_system_health_ring_buffer_recorded | long | Timestamp scheduler monitor system health ring buffer recorded. |
| total_memory_free_block_emergency_descriptors | long | Total memory free block emergency descriptors. |
| total_page_file_kb | long | Total page file kb. |
| total_physical_memory_kb | long | Total physical memory kb. |
| total_virtual_address_space_kb | long | Total virtual address space kb. |
| user_mode_time | long | User mode time timestamp. |
| user_mode_time_ms | long | User mode time ms in milliseconds. |
| wait_result | long | Wait result. |
| wall_clock_time_ms | long | Wall clock time ms in milliseconds. |
| worker | string | Worker. |
| worker_utilization | long | Worker utilization. |
| worker_wait_stats | string | Worker wait stats. |
| working_set_delta | long | Working set delta. |
| yields | long | Yields. |

## MonSqlSecurityService — SQL Security Service

**Purpose**: SQL Security Service. Used to troubleshoot alerts, health transitions, dumps, crashes, and platform error signals. Referenced in MI template areas: availability.
**Category**: Monitoring

| Column | Type | Description |
|--------|------|-------------|
| Level | long | Level. |
| Name | string | Object or resource name. |
| OneBoxClusterId | string | One Box Cluster Id. |
| Pid | long | Pid. |
| Tid | long | Tid. |
| Timestamp | string | timestamp. |
| _name | string | Name. |
| action | string | Action. |
| body | string | Body. |
| callback | string | Callback. |
| cert_alias | string | Cert alias. |
| certificate_name | string | Certificate name. |
| chosen_certificate_thumbprint | string | Chosen certificate thumbprint. |
| client_description | string | Client description. |
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| component | string | Component. |
| connection_id | string | Connection identifier. |
| duration | long | Duration. |
| elapsed_time_milliseconds | real | Elapsed duration in milliseconds. |
| event | string | Event name emitted by the component. |
| exception_message | string | Exception message. |
| exception_stack_trace | string | Exception stack trace. |
| exception_type | string | Type classification for exception. |
| expiry_date | datetime | Expiry date. |
| generationId | long | Generation Id. |
| invalid_certificate_thumbprint | string | Invalid certificate thumbprint. |
| is_emergency | bool | Boolean flag indicating whether emergency. |
| is_fully_connected | bool | Boolean flag indicating whether fully connected. |
| is_operation_successful | bool | Boolean flag indicating whether operation successful. |
| is_phasing_onboarding | bool | Boolean flag indicating whether phasing onboarding. |
| is_valid | bool | Boolean flag indicating whether valid. |
| issue_details | string | Issue details. |
| issuer | string | Issuer. |
| message | string | Human-readable message text. |
| new_state | string | State value for new. |
| new_status | string | Status value for new. |
| old_state | string | State value for old. |
| onboarding_phase | string | Onboarding phase. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| port | long | Port. |
| process_id | long | Process identifier. |
| process_name | string | Process name. |
| purpose | string | Purpose. |
| reg_entry_key | string | Reg entry key. |
| request_id | string | Request identifier used to correlate the operation. |
| res_status_code | string | Res status code. |
| resource_name | string | Resource name. |
| retry_count | long | Number of retry. |
| rollover_required | bool | Boolean flag indicating whether rollover required. |
| self_signed | bool | Boolean flag indicating whether self signed. |
| service_name | string | Service name. |
| sessionName | string | Session Name. |
| severityNumber | long | Severity Number. |
| severityText | string | Severity Text. |
| stack_trace | string | Stack trace. |
| subbed_to_rollovers | bool | Boolean flag indicating whether subbed to rollovers. |
| subject_name | string | Subject name. |
| success | bool | Boolean flag indicating whether success. |
| thumbprint | string | Thumbprint. |
| thumbprint2 | string | Thumbprint2. |
| thumbprint_count | long | Number of thumbprint. |
| thumbprints | string | Thumbprints. |
| trusted_sans | string | Trusted sans. |
| trusted_thumbprints | string | Trusted thumbprints. |
| value | string | Value. |
| workflow_uri | string | Workflow uri. |

## MonSQLSystemHealth — SQL system health and ring-buffer style diagnostics

**Purpose**: SQL system health and ring-buffer style diagnostics. Used to troubleshoot alerts, health transitions, dumps, crashes, and platform error signals. Referenced in MI template areas: availability, backup-restore, general, networking, performance. Often used when validating audit setup or audit runtime behavior. Often used during backup or restore investigations.
**Category**: Monitoring

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| TridentServerType | string | Trident Server Type. |
| address | string | Address. |
| affinity_mask | long | Affinity mask. |
| allocation_potential_memory_mb | long | Allocation potential memory mb. |
| allocation_size | long | Allocation size. |
| allocation_type | string | Type classification for allocation. |
| available_physical_memory_mb | long | Available physical memory mb. |
| backup_lsn | string | Backup lsn. |
| binary_path_name | string | Binary path name. |
| buffer_pool_clock_stats | string | Buffer pool clock stats. |
| call_stack | string | Call stack. |
| callstack | string | Callstack. |
| callstack_rva | string | Callstack rva. |
| checkpoint_lsn | string | Checkpoint lsn. |
| class | string | Class. |
| code_package_start_time | long | Code package start time timestamp. |
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| committed_mb | long | Committed mb. |
| committed_target_mb | long | Committed target mb. |
| component | string | Component. |
| continue_wait | bool | Boolean flag indicating whether continue wait. |
| critical_level | string | Critical level. |
| current_job_cap_mb | long | Current job cap mb. |
| database_id | long | Database identifier. |
| db_id | long | Database identifier. |
| destroy_count | long | Number of destroy. |
| distributed_statement_id | string | Distributed statement identifier. |
| duration | long | Duration. |
| end_time | datetime | End timestamp. |
| error_code | long | Numeric error code for the failure or event. |
| error_id | long | Error identifier. |
| event | string | Event name emitted by the component. |
| event_handle | string | Event handle. |
| event_id | long | Event identifier. |
| exclusive_count | long | Number of exclusive. |
| exit_code | long | Exit code. |
| file_handle | string | File handle. |
| file_id | long | File identifier. |
| file_path | string | File path. |
| has_waiters | bool | Boolean flag indicating whether has waiters. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| http_status | long | Status value for http. |
| id | long | identifier. |
| instance_partition_id | string | Instance partition identifier. |
| instance_replica_id | long | Instance replica identifier. |
| instance_rg_size | string | Instance resource governor size. |
| is_non_sos_usage_leaked | bool | Boolean flag indicating whether non sos usage leaked. |
| is_poisoned | bool | Boolean flag indicating whether poisoned. |
| is_superlatch | bool | Boolean flag indicating whether superlatch. |
| keep_count | long | Number of keep. |
| kernel_mode_time | long | Kernel mode time timestamp. |
| last_long_io_offset | long | Last long I/O offset. |
| leaked_memory_clerk | string | Leaked memory clerk. |
| logical_database_guid | string | Logical database guid. |
| logical_database_id | string | Logical database identifier. |
| logical_db_id | string | Logical database identifier. |
| longer_than_sec | long | Longer than sec. |
| memory_allocated | long | Memory allocated. |
| memory_pressure_level | long | Memory pressure level. |
| memory_utilization | long | Memory utilization. |
| message | string | Human-readable message text. |
| message_sub_type | long | Type classification for message sub. |
| message_type | string | Type classification for message. |
| min_skip_lsn | string | Minimum skip lsn. |
| mode | string | Mode. |
| new_affinity_mask | long | New affinity mask. |
| new_diff_baseline_lsn | string | New diff baseline lsn. |
| new_log_chain_backup_lsn | string | New log chain backup lsn. |
| new_log_chain_origin_lsn | string | New log chain origin lsn. |
| node_id | long | Node identifier. |
| non_sos_usage_mb | long | Non sos usage mb. |
| occurrences | long | Occurrences. |
| old_affinity_mask | long | Old affinity mask. |
| oldest_xact_lsn | string | Oldest xact lsn. |
| oom_cause | long | OOM cause. |
| oom_factor | long | OOM factor. |
| oom_memory_pool | string | OOM memory pool. |
| opcode | string | Opcode. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| page_faults | long | Page faults. |
| page_id | long | Page identifier. |
| phase_completion_duration_ms | long | Phase completion duration ms in milliseconds. |
| phase_start_timestamp | datetime | Phase start timestamp. |
| physical_database_id | string | Physical database identifier. |
| physical_db_id | string | Physical database identifier. |
| pool_id | string | Pool identifier. |
| process_id | long | Process identifier. |
| process_memory_usage_mb | long | Process memory usage mb. |
| process_utilization | long | Process utilization. |
| reconfig_result | long | Reconfig result. |
| scheduler | long | Scheduler. |
| scheduler_id | long | Scheduler identifier. |
| sessionName | string | Session Name. |
| session_id | long | Session identifier. |
| shared_count | long | Number of shared. |
| shutdown_option | string | Shutdown option. |
| start_time | long | Start timestamp. |
| starting_address | string | Starting address. |
| startup_phase_name | string | Startup phase name. |
| system_idle | long | System idle. |
| system_thread | string | System thread. |
| task_owner | string | Task owner. |
| task_owner_callstack | string | Task owner callstack. |
| task_owner_wait_type | string | Type classification for task owner wait. |
| timestamp_nonpreemptive_long_syncio | long | Timestamp nonpreemptive long syncio. |
| timestamp_scheduler_monitor_deadlock_ring_buffer_recorded | long | Timestamp scheduler monitor deadlock ring buffer recorded. |
| timestamp_scheduler_monitor_non_yielding_iocp_ring_buffer_recor | long | Timestamp scheduler monitor non yielding iocp ring buffer recor. |
| timestamp_scheduler_monitor_non_yielding_ring_buffer_recorded | long | Timestamp scheduler monitor non yielding ring buffer recorded. |
| timestamp_scheduler_monitor_non_yielding_rm_ring_buffer_recorde | long | Timestamp scheduler monitor non yielding rm ring buffer recorde. |
| timestamp_scheduler_monitor_stalled_dispatcher_ring_buffer_reco | long | Timestamp scheduler monitor stalled dispatcher ring buffer reco. |
| timestamp_scheduler_monitor_system_health_ring_buffer_recorded | long | Timestamp scheduler monitor system health ring buffer recorded. |
| top_memory_clerks | string | Top memory clerks. |
| top_memory_pools | string | Top memory pools. |
| update_count | long | Number of update. |
| url | string | Url. |
| user_data_pointer | string | User data pointer. |
| user_mode_time | long | User mode time timestamp. |
| verb | string | Verb. |
| wait_result | long | Wait result. |
| worker | string | Worker. |
| worker_address | string | Worker address. |
| worker_utilization | long | Worker utilization. |
| working_set_delta | long | Working set delta. |
| yields | long | Yields. |

## MonSystemEventLogErrors — System Event Log Errors

**Purpose**: System Event Log Errors. Used to troubleshoot alerts, health transitions, dumps, crashes, and platform error signals. Referenced in MI template areas: performance.
**Category**: Monitoring

| Column | Type | Description |
|--------|------|-------------|
| EventDescription | string | Event Description. |
| EventID | string | Event ID. |
| Level | long | Level. |
| OneBoxClusterId | string | One Box Cluster Id. |
| ProviderName | string | Provider Name. |

# 8. Infrastructure & Provisioning

## MonChangeManagedServerInstanceReqs — Change Managed Server Instance Reqs

**Purpose**: Change Managed Server Instance Reqs. Used to investigate platform automation, deployment, cluster configuration, and provisioning workflows. Referenced in MI template areas: availability, networking.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| code_package_version | string | Code package version. |
| concurrency_token | long | Concurrency token. |
| create_time | datetime | Creation timestamp. |
| end_utc_date | datetime | End utc date. |
| fsm_context_instance_name | string | Fsm context instance name. |
| fsm_extension_data | string | Fsm extension data. |
| fsm_instance_id | string | Fsm instance identifier. |
| fsm_timer_event_version | long | Fsm timer event version. |
| fsm_version | long | Fsm version. |
| is_error_state | long | Boolean flag indicating whether error state. |
| is_reattach | long | Boolean flag indicating whether reattach. |
| is_stable_state | long | Boolean flag indicating whether stable state. |
| last_exception | string | Last exception. |
| last_state_change_time | datetime | Last state change time timestamp. |
| last_update_time | datetime | Last update time timestamp. |
| managed_server_id | string | Managed Instance identifier. |
| mode | string | Mode. |
| next_successor | long | Next successor. |
| request_id | string | Request identifier used to correlate the operation. |
| requested_custom_maintenance_window_scheduler_pattern | string | Requested custom maintenance window scheduler pattern. |
| requested_maintenance_policy_id | string | Requested maintenance policy identifier. |
| requested_managed_instance_pool_id | string | Requested managed instance pool identifier. |
| requested_target_reserved_storage_iops | long | Requested target reserved storage IOPS. |
| requested_target_reserved_storage_size_gb | long | Requested target reserved storage size gb. |
| requested_target_reserved_storage_throughput_mbps | long | Requested target reserved storage throughput mbps. |
| requested_target_service_level_objective | string | Requested target service level objective. |
| requested_target_storage_account_tag | string | Requested target storage account tag. |
| requested_target_storage_account_type | string | Type classification for requested target storage account. |
| requested_target_subnet_id | string | Requested target subnet identifier. |
| requested_target_subscription_affinity_tag | string | Requested target subscription affinity tag. |
| requested_target_tenant_ring_name | string | Requested target tenant ring name. |
| requested_target_worker_service_affinity_tag | string | Requested target worker service affinity tag. |
| rollback_transactions_start_time | datetime | Rollback transactions start time timestamp. |
| source_cluster_vnet_dns_record_name | string | Source cluster vnet dns record name. |
| source_managed_server_is_wcow | long | Source managed server is wcow. |
| source_managed_server_using_md | long | Source managed server using md. |
| source_sql_instance_name | string | Source SQL instance name. |
| source_zone_redundancy | long | Source zone redundancy. |
| start_utc_date | datetime | Start utc date. |
| state | string | Current lifecycle or health state. |
| storage_account_created_in_this_request | long | Storage account created in this request. |
| storage_container_created_in_this_request | long | Storage container created in this request. |
| target_cluster_vnet_dns_record_name | string | Target cluster vnet dns record name. |
| target_managed_server_is_wcow | long | Target managed server is wcow. |
| target_managed_server_using_md | long | Target managed server using md. |
| target_sql_instance_name | string | Target SQL instance name. |
| target_zone_redundancy | long | Target zone redundancy. |

## MonClusterLoad — Cluster Load

**Purpose**: Cluster Load. Used to investigate platform automation, deployment, cluster configuration, and provisioning workflows. Referenced in MI template areas: availability, networking, performance.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| Level | long | Level. |
| Name | string | Object or resource name. |
| OneBoxClusterId | string | One Box Cluster Id. |
| Pid | long | Pid. |
| SnapshotTimestamp | datetime | Snapshot timestamp. |
| Tid | long | Tid. |
| Timestamp | string | timestamp. |
| _name | string | Name. |
| aggregated_capacity | long | Aggregated capacity. |
| body | string | Body. |
| capacity | long | Capacity. |
| capacity_report_type | string | Type classification for capacity report. |
| code_package_version | string | Code package version. |
| code_version | string | Code version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| config_version | string | Config version. |
| event | string | Event name emitted by the component. |
| exception_scrubbed | string | Exception scrubbed. |
| fault_domain | string | Fault domain. |
| fault_domain_count | long | Number of fault domain. |
| health_state | string | State value for health. |
| is_seed_node | bool | Boolean flag indicating whether seed node. |
| load | long | Load. |
| message_scrubbed | string | Message scrubbed. |
| metric_name | string | Metric name. |
| node_status | string | Status value for node. |
| node_type | string | Type classification for node. |
| node_up_time | string | Node up time timestamp. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| process_id | long | Process identifier. |
| role_count | long | Number of role. |
| role_name | string | Role name. |
| service_count | long | Number of service. |
| sessionName | string | Session Name. |
| severityNumber | long | Severity Number. |
| severityText | string | Severity Text. |
| sf_capacity | long | Sf capacity. |
| sf_load | long | Sf load. |
| tenant_ring_name | string | Tenant ring name. |
| upgrade_domain | string | Upgrade domain. |
| upgrade_domain_count | long | Number of upgrade domain. |
| vm_size | string | Vm size. |

## MonConfigAppTypeOverrides — Config App Type Overrides

**Purpose**: Config App Type Overrides. Used to investigate platform automation, deployment, cluster configuration, and provisioning workflows. Referenced in MI template areas: backup-restore.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| application_type_name | string | Application type name. |
| code_package_version | string | Code package version. |
| config_package_name | string | Config package name. |
| contact_dl | string | Contact dl. |
| description | string | Description. |
| end_utc_date | datetime | End utc date. |
| fabric_cluster_name | string | Fabric cluster name. |
| justification | string | Justification. |
| last_update_time | datetime | Last update time timestamp. |
| override_value | string | Override value. |
| override_value_scope | string | Override value scope. |
| section_name | string | Section name. |
| service_manifest_name | string | Service manifest name. |
| setting_name | string | Setting name. |
| stage | string | Stage. |
| start_utc_date | datetime | Start utc date. |

## MonConfigLogicalServerOverrides — Config Logical Server Overrides

**Purpose**: Config Logical Server Overrides. Used to investigate platform automation, deployment, cluster configuration, and provisioning workflows. Referenced in MI template areas: backup-restore.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| Category | string | Category. |
| Logical_Server_Name | string | Managed Instance server name. |
| PartitionId | string | Partition Id. |
| Property_Justification | string | Property Justification. |
| Property_Name | string | Property Name. |
| Property_User | string | Property User. |
| Property_Value | string | Property Value. |
| code_package_version | string | Code package version. |
| end_utc_date | datetime | End utc date. |
| start_utc_date | datetime | Start utc date. |

## MonDeploymentAutomation — Deployment Automation

**Purpose**: Deployment Automation. Used to investigate platform automation, deployment, cluster configuration, and provisioning workflows. Referenced in MI template areas: availability, backup-restore.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| component | string | Component. |
| event | string | Event name emitted by the component. |
| exception | string | Exception. |
| message | string | Human-readable message text. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| partition_id | string | Partition identifier. |
| process_id | long | Process identifier. |
| service_address | string | Service address. |
| service_name | string | Service name. |
| service_type | string | Type classification for service. |
| sessionName | string | Session Name. |
| severity | string | Severity level associated with the event. |
| stack_trace | string | Stack trace. |
| version | string | Version. |

## MonDeploymentAutomationInstances — Deployment Automation Instances

**Purpose**: Deployment Automation Instances. Used to investigate platform automation, deployment, cluster configuration, and provisioning workflows. Referenced in MI template areas: availability.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| cmdlet_exception | string | Cmdlet exception. |
| code_package_version | string | Code package version. |
| concurrency_token | long | Concurrency token. |
| control_ring_name | string | Control ring name. |
| create_time | datetime | Creation timestamp. |
| current_progress | string | Current progress. |
| current_progress_update_time | datetime | Current progress update time timestamp. |
| deployment_id | string | Deployment identifier. |
| end_utc_date | datetime | End utc date. |
| fabric_application_uri | string | Fabric application uri. |
| fabric_service_uri | string | Fabric service uri. |
| fsm_context_instance_name | string | Fsm context instance name. |
| fsm_extension_data | string | Fsm extension data. |
| fsm_instance_id | string | Fsm instance identifier. |
| fsm_timer_event_version | long | Fsm timer event version. |
| fsm_version | long | Fsm version. |
| instance_id | string | Instance identifier. |
| is_automitigation_enabled | long | Boolean flag indicating whether automitigation enabled. |
| is_error_state | long | Boolean flag indicating whether error state. |
| is_stable_state | long | Boolean flag indicating whether stable state. |
| last_exception | string | Last exception. |
| last_state_change_time | datetime | Last state change time timestamp. |
| last_update_time | datetime | Last update time timestamp. |
| next_successor | long | Next successor. |
| request_id | string | Request identifier used to correlate the operation. |
| requested_application_type_version | string | Requested application type version. |
| scenario_class_name | string | Scenario class name. |
| scenario_parameters | string | Scenario parameters. |
| scenario_parameters_overrides | string | Scenario parameters overrides. |
| start_utc_date | datetime | Start utc date. |
| state | string | Current lifecycle or health state. |

## MonFabricApi — Fabric Api

**Purpose**: Fabric Api. Used to investigate platform automation, deployment, cluster configuration, and provisioning workflows. Referenced in MI template areas: availability, general. Often used during failover or replica troubleshooting. Often used to correlate SQL behavior with Service Fabric activity.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| api_name | string | Api name. |
| attach_activity_id | string | Attach activity identifier. |
| attach_activity_id_xfer | string | Attach activity id xfer. |
| bucket_hint | string | Bucket hint. |
| catch_up_capability_other | long | Catch up capability other. |
| catch_up_mode | long | Catch up mode. |
| catch_up_mode_desc | string | Catch up mode desc. |
| code_package_start_time | long | Code package start time timestamp. |
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| current_progress_other | long | Current progress other. |
| current_state | long | State value for current. |
| current_state_desc | string | Current state desc. |
| current_write_status | long | Status value for current write. |
| current_write_status_desc | string | Current write status desc. |
| dump_class | string | Dump class. |
| dump_options | string | Dump options. |
| duration | long | Duration. |
| epoch_configuration_number | long | Epoch configuration number. |
| epoch_data_loss_number | long | Epoch data loss number. |
| error_code | long | Numeric error code for the failure or event. |
| error_message | string | Error message. |
| error_severity | long | Error severity. |
| error_state | long | State value for error. |
| event | string | Event name emitted by the component. |
| fabric_replica_id | long | Fabric replica identifier. |
| fabric_replica_id_other | long | Fabric replica id other. |
| fault_callstack_rva | string | Fault callstack rva. |
| fault_reason | long | Fault reason. |
| fault_reason_desc | string | Fault reason desc. |
| fault_type | long | Type classification for fault. |
| fault_type_desc | string | Fault type desc. |
| from_sequence_number | long | From sequence number. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| initialization_data | string | Initialization data. |
| instance | string | Instance. |
| instance_id | long | Instance identifier. |
| last_sequence_number | long | Last sequence number. |
| logical_database_id | string | Logical database identifier. |
| message | string | Human-readable message text. |
| must_catch_up_replica_count | long | Number of must catch up replica. |
| must_catchup_replica_count | long | Number of must catchup replica. |
| new_role | long | New role. |
| new_role_desc | string | New role desc. |
| opcode | string | Opcode. |
| open_mode | long | Open mode. |
| open_mode_desc | string | Open mode desc. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| partition_id | string | Partition identifier. |
| physical_database_id | string | Physical database identifier. |
| previous_write_status | long | Status value for previous write. |
| previous_write_status_desc | string | Previous write status desc. |
| process_id | long | Process identifier. |
| replica_count_current | long | Replica count current. |
| replica_count_previous | long | Replica count previous. |
| replica_id | string | Replica identifier. |
| replica_infos_current | string | Replica infos current. |
| replica_infos_mustcatchup | string | Replica infos mustcatchup. |
| replica_infos_previous | string | Replica infos previous. |
| replica_role | string | Replica role. |
| replicator_address_other | string | Replicator address other. |
| result | long | Result. |
| result_desc | string | Result desc. |
| role_other | long | Role other. |
| role_other_desc | string | Role other desc. |
| seeding_performed | bool | Boolean flag indicating whether seeding performed. |
| service_address | string | Service address. |
| service_name | string | Service name. |
| service_type | string | Type classification for service. |
| sessionName | string | Session Name. |
| system_thread_id | long | System thread identifier. |
| target_replica_set_size | long | Target replica set size. |
| work_id | long | Work identifier. |
| write_quorum_current | long | Write quorum current. |
| write_quorum_previous | long | Write quorum previous. |

## MonFabricClusters — Fabric Clusters

**Purpose**: Fabric Clusters. Used to investigate platform automation, deployment, cluster configuration, and provisioning workflows. Referenced in MI template areas: availability, networking. Often used to correlate SQL behavior with Service Fabric activity.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| batched_winfab_and_infra_enabled | long | Batched winfab and infra enabled. |
| batched_winfab_and_infra_status_justification | string | Batched winfab and infra status justification. |
| batched_winfab_not_advanced_reason | string | Batched winfab not advanced reason. |
| code_package_version | string | Code package version. |
| concurrency_token | long | Concurrency token. |
| create_time | datetime | Creation timestamp. |
| custom_maintenance_last_notification | string | Custom maintenance last notification. |
| custom_maintenance_next_window_end_time_utc | datetime | Custom maintenance next window end time utc. |
| custom_maintenance_next_window_start_time_utc | datetime | Custom maintenance next window start time utc. |
| custom_maintenance_notification_enabled | long | Custom maintenance notification enabled. |
| custom_maintenance_protected_ring | long | Custom maintenance protected ring. |
| custom_maintenance_reason | string | Custom maintenance reason. |
| custom_maintenance_window_enabled | long | Custom maintenance window enabled. |
| custom_maintenance_window_recurring_pattern | string | Custom maintenance window recurring pattern. |
| custom_no_fly_zone_end_time_utc | datetime | Custom no fly zone end time utc. |
| custom_no_fly_zone_start_time_utc | datetime | Custom no fly zone start time utc. |
| deployment_id | string | Deployment identifier. |
| deployment_id_replaced_sequence | long | Deployment id replaced sequence. |
| deployment_id_sequence | long | Deployment id sequence. |
| enable_custom_maintenance_orchestration | long | Enable custom maintenance orchestration. |
| enable_wise_upgrades | long | Enable wise upgrades. |
| encryption_keys | string | Encryption keys. |
| end_utc_date | datetime | End utc date. |
| fsm_context_instance_name | string | Fsm context instance name. |
| fsm_extension_data | string | Fsm extension data. |
| fsm_instance_id | string | Fsm instance identifier. |
| fsm_timer_event_version | long | Fsm timer event version. |
| fsm_version | long | Fsm version. |
| hosted_service_dns_name | string | Hosted service dns name. |
| hosted_service_name | string | Hosted service name. |
| hosted_service_pinned_cluster_name | string | Hosted service pinned cluster name. |
| hosted_service_subscription_id | string | Hosted service subscription identifier. |
| image_store_account_name | string | Image store account name. |
| image_store_container_name | string | Image store container name. |
| infra_job_throttle_setting | string | Infra job throttle setting. |
| infra_payload_tracking_data | string | Infra payload tracking data. |
| infrastructure_configuration_version | string | Infrastructure configuration version. |
| ipv4_address | string | Ipv4 address. |
| ipv6_address | string | Ipv6 address. |
| is_error_state | long | Boolean flag indicating whether error state. |
| is_multi_hosted_service | long | Boolean flag indicating whether multi hosted service. |
| is_paas_v2 | long | Boolean flag indicating whether paas v2. |
| is_stable_state | long | Boolean flag indicating whether stable state. |
| last_deployment_garbage_collection_attempt_time_utc | datetime | Last deployment garbage collection attempt time utc. |
| last_deployment_garbage_collection_time_utc | datetime | Last deployment garbage collection time utc. |
| last_exception | string | Last exception. |
| last_infra_upgrade_rollout_key | string | Last infra upgrade rollout key. |
| last_infra_upgrade_time | datetime | Last infra upgrade time timestamp. |
| last_placement_update_time | datetime | Last placement update time timestamp. |
| last_state_change_time | datetime | Last state change time timestamp. |
| last_update_time | datetime | Last update time timestamp. |
| maintenance_properties | string | Maintenance properties. |
| name | string | Object or resource name. |
| next_successor | long | Next successor. |
| ongoing_impactful_deployments | string | Ongoing impactful deployments. |
| opted_out_from_he_updates | long | Opted out from he updates. |
| pause_flighting | long | Pause flighting. |
| pending_upgrade_cluster_manifest_version | string | Pending upgrade cluster manifest version. |
| pending_upgrade_msi_version | string | Pending upgrade msi version. |
| platform_batching_enabled | long | Platform batching enabled. |
| private_dns_name | string | Private dns name. |
| processed_fabric_uri | string | Processed fabric uri. |
| processed_property_name | string | Processed property name. |
| product_family | string | Product family. |
| request_id | string | Request identifier used to correlate the operation. |
| scheduler_name | string | Scheduler name. |
| sfrp_arm_deployment_status | string | Status value for sfrp arm deployment. |
| sql_mi_dng_id | string | SQL MI dng identifier. |
| start_utc_date | datetime | Start utc date. |
| state | string | Current lifecycle or health state. |
| time_zone | string | Time zone. |
| winfab_infra_block_requests | string | Winfab infra block requests. |
| winfab_infra_jobs | string | Winfab infra jobs. |
| winfab_infra_status | string | Status value for winfab infra. |
| winfab_upgrade_info | string | Winfab upgrade info. |
| winfab_upgrade_status | string | Status value for winfab upgrade. |
| wise_infra_enabled | long | Wise infra enabled. |
| wise_infra_next_operation | string | Wise infra next operation. |
| wise_infra_next_operation_time | datetime | Wise infra next operation time timestamp. |
| wise_infra_status_justification | string | Wise infra status justification. |
| wise_upgrades_reason | string | Wise upgrades reason. |
| wise_winfab_upgrade_next_operation | string | Wise winfab upgrade next operation. |
| wise_winfab_upgrade_next_operation_time | datetime | Wise winfab upgrade next operation time timestamp. |
| wise_winfab_upgrade_status_justification | string | Wise winfab upgrade status justification. |
| wise_winfab_upgrades_enabled | long | Wise winfab upgrades enabled. |
| workload_distribution_polling_timer_due_time | datetime | Workload distribution polling timer due time timestamp. |
| workload_statistics | string | Workload statistics. |
| zones_for_data_plane_placement | long | Zones for data plane placement. |

## MonFabricDebug — Fabric Debug

**Purpose**: Fabric Debug. Used to investigate platform automation, deployment, cluster configuration, and provisioning workflows. Referenced in MI template areas: availability, general. Often used to correlate SQL behavior with Service Fabric activity.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| acknowledgment_number | long | Acknowledgment number. |
| action | string | Action. |
| active_workers | long | Active workers. |
| ag_database_id | string | Ag database identifier. |
| ag_id | string | Ag identifier. |
| associated_object_id | long | Associated object identifier. |
| async_callback | string | Async callback. |
| async_operation_context | string | Async operation context. |
| attach_activity_id | string | Attach activity identifier. |
| attach_activity_id_xfer | string | Attach activity id xfer. |
| availability_group_id | string | Availability group identifier. |
| availability_replica_id | string | Availability replica identifier. |
| bucket_hint | string | Bucket hint. |
| build_barrier_info_count | long | Number of build barrier info. |
| build_canceled | bool | Boolean flag indicating whether build canceled. |
| cas_action | string | Cas action. |
| catchup_queue_size | long | Catchup queue size. |
| code_package_start_time | long | Code package start time timestamp. |
| code_package_version | string | Code package version. |
| commit_policy | string | Commit policy. |
| commit_policy_target | string | Commit policy target. |
| config_count | long | Number of config. |
| configuration_number | long | Configuration number. |
| connection_session_id | string | Connection session identifier. |
| current_state | string | State value for current. |
| current_version | long | Current version. |
| database_id | long | Database identifier. |
| database_name | string | Database name. |
| database_replica_id | string | Database replica identifier. |
| dataloss_number | long | Dataloss number. |
| db_id | long | Database identifier. |
| dbmgr_object_type | string | Type classification for dbmgr object. |
| debug_trace | string | Debug trace. |
| delay | long | Delay. |
| dump_class | string | Dump class. |
| dump_options | string | Dump options. |
| duration | long | Duration. |
| duration_sec | long | Duration sec. |
| elapsed_time_in_millisec | long | Elapsed time in millisec. |
| elapsed_time_in_secs | long | Elapsed time in secs. |
| end_of_log | string | End of log. |
| endpoint | string | Endpoint. |
| endpoint_bag_element_semaphore_count | long | Number of endpoint bag element semaphore. |
| endpoint_bag_elements | long | Endpoint bag elements. |
| endpoint_bag_max_elements | long | Endpoint bag max elements. |
| endpoint_sync_type | string | Type classification for endpoint sync. |
| epoch_configuration_number | long | Epoch configuration number. |
| epoch_data_loss_number | long | Epoch data loss number. |
| error_code | long | Numeric error code for the failure or event. |
| error_number | long | SQL or platform error number. |
| error_severity | long | Error severity. |
| error_state | long | State value for error. |
| event | string | Event name emitted by the component. |
| event_hadr_fabric_endpoint_sync | long | Event HADR fabric endpoint sync. |
| event_name | string | Event name. |
| event_number | long | Event number. |
| fabric_replica_id | long | Fabric replica identifier. |
| failure_reason | string | Failure reason. |
| file_binding_id | string | File binding identifier. |
| file_id | long | File identifier. |
| file_path | string | File path. |
| final_file_size_mb | long | Final file size mb. |
| flushed_log | string | Flushed log. |
| freshness_number | long | Freshness number. |
| geo_truncation_holdup_threshold | long | Geo truncation holdup threshold. |
| group_id | string | Group identifier. |
| hadr_truncation_block | string | HADR truncation block. |
| holdup_due_to_secondary_partner | long | Holdup due to secondary partner. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| idle_workers | long | Idle workers. |
| initial_file_size_mb | long | Initial file size mb. |
| is_local | bool | Boolean flag indicating whether local. |
| is_primary | bool | Boolean flag indicating whether primary. |
| is_successful | bool | Boolean flag indicating whether successful. |
| is_using_ctr_pvs_in_xact | bool | Boolean flag indicating whether using ctr pvs in xact. |
| is_valid | bool | Boolean flag indicating whether valid. |
| lag_id | string | Lag identifier. |
| lag_replica_id | string | Lag replica identifier. |
| lag_role | string | Lag role. |
| last_lsn | string | Last lsn. |
| last_lsn_received | string | Last lsn received. |
| link_type | string | Type classification for link. |
| link_version | long | Link version. |
| local_availability_replica_id | string | Local availability replica identifier. |
| lock_skip_efficiency | real | Lock skip efficiency. |
| lockspace_nest_id | long | Lockspace nest identifier. |
| lockspace_sub_id | long | Lockspace sub identifier. |
| lockspace_workspace_id | string | Lockspace workspace identifier. |
| log_backup_lsn | string | Log backup lsn. |
| log_block_id | long | Log block identifier. |
| log_truncation_block | string | Log truncation block. |
| logical_database_id | string | Logical database identifier. |
| logical_database_name | string | Logical database name. |
| major | long | Major. |
| max_achievable_lock_skip_efficiency | real | Maximum achievable lock skip efficiency. |
| max_potential_skipped_locks | long | Maximum potential skipped locks. |
| max_version | long | Maximum version. |
| message | string | Human-readable message text. |
| message_log_id | string | Message log identifier. |
| message_type | string | Type classification for message. |
| metric_name | string | Metric name. |
| min_lsn | string | Minimum lsn. |
| min_version | long | Minimum version. |
| minimum_skip_lsn | string | Minimum skip lsn. |
| minor | long | Minor. |
| mode | string | Mode. |
| msg_source | string | Msg source. |
| new_state | long | State value for new. |
| new_state_desc | string | New state desc. |
| notify_on_copy_complete | bool | Boolean flag indicating whether notify on copy complete. |
| notify_on_role_change | bool | Boolean flag indicating whether notify on role change. |
| notify_on_sync_state_reached | bool | Boolean flag indicating whether notify on sync state reached. |
| num_forks_in_message | long | Num forks in message. |
| object_id | long | Object identifier. |
| old_state | long | State value for old. |
| old_state_desc | string | Old state desc. |
| opcode | string | Opcode. |
| operation | string | Operation. |
| operation_id | string | Operation identifier for the workflow. |
| operation_reason | string | Operation reason. |
| operation_type | long | Type classification for operation. |
| operation_type_desc | string | Operation type desc. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| owner_type | string | Type classification for owner. |
| package | string | Package. |
| page_id | long | Page identifier. |
| page_lsn | string | Page lsn. |
| partition_id | string | Partition identifier. |
| partner_qds_endpoint | string | Partner Query Store endpoint. |
| partner_replica_id | string | Partner replica identifier. |
| physical_database_id | string | Physical database identifier. |
| physical_database_name | string | Physical database name. |
| physical_db_name | string | Physical database name. |
| process_id | long | Process identifier. |
| proposed_state | string | State value for proposed. |
| reason | string | Reason. |
| reason_desc | string | Reason desc. |
| received_lsn | string | Received lsn. |
| recovery_point | string | Recovery point. |
| redo_lsn | string | Redo lsn. |
| redo_point | string | Redo point. |
| redo_time | string | Redo time timestamp. |
| registered | bool | Boolean flag indicating whether registered. |
| remote_endpoint_url | string | Remote endpoint url. |
| remote_replica_id | string | Remote replica identifier. |
| replica_event_type | long | Type classification for replica event. |
| replica_event_type_desc | string | Replica event type desc. |
| replica_id | string | Replica identifier. |
| replication_endpoint | string | Replication endpoint. |
| replication_type | string | Type classification for replication. |
| request_id | string | Request identifier used to correlate the operation. |
| request_payload | string | Request payload. |
| reseed_reason | string | Reseed reason. |
| reseed_threshold | long | Reseed threshold. |
| resource_0 | long | Resource 0. |
| resource_1 | long | Resource 1. |
| resource_2 | long | Resource 2. |
| resource_description | string | Resource description. |
| resource_type | string | Type classification for resource. |
| restart_reason | string | Restart reason. |
| result | long | Result. |
| result_desc | string | Result desc. |
| retry_times | long | Retry times. |
| secondary_availability_replica_id | string | Secondary availability replica identifier. |
| secondary_truncation_lsn | string | Secondary truncation lsn. |
| sequence_number | long | Sequence number. |
| server_name | string | Managed Instance server name. |
| service_name | string | Service name. |
| sessionName | string | Session Name. |
| session_id | string | Session identifier. |
| severity | long | Severity level associated with the event. |
| skipped_locks | long | Skipped locks. |
| slog_skipped_locks | long | Slog skipped locks. |
| stack_bottom_lsn | string | Stack bottom lsn. |
| stack_version | long | Stack version. |
| state | long | Current lifecycle or health state. |
| status | string | Current status reported by the component. |
| storage_type | long | Type classification for storage. |
| storage_type_desc | string | Storage type desc. |
| sub_step | string | Sub step. |
| subscriber_type | long | Type classification for subscriber. |
| subscriber_type_desc | string | Subscriber type desc. |
| success | bool | Boolean flag indicating whether success. |
| sync_log_block | long | Sync log block. |
| sync_state | string | State value for sync. |
| synchronization_barrier_id | string | Synchronization barrier identifier. |
| system_thread_id | long | System thread identifier. |
| target_availability_replica_id | string | Target availability replica identifier. |
| target_state | string | State value for target. |
| task_id | string | Task identifier. |
| task_name | string | Task name. |
| task_state | string | State value for task. |
| task_type | string | Type classification for task. |
| thread_id | long | Thread identifier. |
| total_locks | long | Total locks. |
| total_locks_to_apply | long | Total locks to apply. |
| total_slog_locks_to_apply | long | Total slog locks to apply. |
| transaction_id | long | Transaction identifier. |
| transaction_name | string | Transaction name. |
| transaction_start_time | datetime | Transaction start time timestamp. |
| transition_count | long | Number of transition. |
| transition_reason | string | Transition reason. |
| transition_time | datetime | Transition time timestamp. |
| trigger | long | Trigger. |
| trigger_desc | string | Trigger desc. |
| truncation_holdup_threshold | long | Truncation holdup threshold. |
| truncation_lsn_without_secondary_partner | string | Truncation lsn without secondary partner. |
| type | string | Type. |
| unique_identifier | string | Unique identifier. |
| wait_time | long | Wait time timestamp. |
| work_id | long | Work identifier. |
| worker_limit | long | Worker limit. |
| worker_start_success | bool | Boolean flag indicating whether worker start success. |
| xdes_id | string | Xdes identifier. |

## MonFabricThrottle — Fabric Throttle

**Purpose**: Fabric Throttle. Used to investigate platform automation, deployment, cluster configuration, and provisioning workflows. Referenced in MI template areas: availability. Often used to correlate SQL behavior with Service Fabric activity.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| attach_activity_id | string | Attach activity identifier. |
| attach_activity_id_xfer | string | Attach activity id xfer. |
| availability_group_id | string | Availability group identifier. |
| availability_replica_id | string | Availability replica identifier. |
| code_package_start_time | long | Code package start time timestamp. |
| code_package_version | string | Code package version. |
| current_log_size | long | Current log size. |
| current_throttle_time | long | Current throttle time timestamp. |
| database_name | string | Database name. |
| database_replica_id | string | Database replica identifier. |
| event | string | Event name emitted by the component. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| is_reseeding_replica | bool | Boolean flag indicating whether reseeding replica. |
| is_seeding_in_progress | bool | Boolean flag indicating whether seeding in progress. |
| is_throttling_happening_due_to_log_size | long | Boolean flag indicating whether throttling happening due to log size. |
| latest_redo_rate | long | Latest redo rate. |
| log_generation_rate_due_to_log_size | long | Log generation rate due to log size. |
| log_holdup_in_bytes_due_to_slow_truncating_secondary_partner | long | Log holdup in size in bytes due to slow truncating secondary partner. |
| log_size_throttling_threshold | long | Log size throttling threshold. |
| log_truncation_holdup | string | Log truncation holdup. |
| max_log_size | long | Maximum log size. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| percent_throttle_open | long | Percent throttle open. |
| process_id | long | Process identifier. |
| redo_queue_size | long | Redo queue size. |
| redo_rate | long | Redo rate. |
| redo_time | long | Redo time timestamp. |
| reseed_threshold | long | Reseed threshold. |
| send_queue_size | long | Send queue size. |
| send_rate | long | Send rate. |
| send_time | long | Send time timestamp. |
| sessionName | string | Session Name. |
| sku_max_log_generation_rate | long | Sku max log generation rate. |
| system_thread_id | long | System thread identifier. |
| throttle_on | bool | Boolean flag indicating whether throttle on. |
| throttle_started | bool | Boolean flag indicating whether throttle started. |
| throttled_log_generation_rate | long | Throttled log generation rate. |
| throttling_progress | long | Throttling progress. |
| throttling_reason | string | Throttling reason. |
| total_throttle_time | long | Total throttle time timestamp. |

## MonManagement — Management-plane operation activity

**Purpose**: Management-plane operation activity. Used to investigate platform automation, deployment, cluster configuration, and provisioning workflows. Referenced in MI template areas: availability, backup-restore, general, networking, performance. Often used during backup or restore investigations.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| IgnoreSafetyCheck | bool | Boolean flag indicating whether Ignore Safety Check. |
| IncludeSeedNode | bool | Boolean flag indicating whether Include Seed Node. |
| ResourceType | string | Resource Type. |
| _all_emails_ids | string | All emails ids. |
| _email_request_ids_Pending_confirmation | string | Email request ids Pending confirmation. |
| _exceptionType | string | Exception Type. |
| _operationStatusCode | string | Operation Status Code. |
| aad_only_auth | bool | Boolean flag indicating whether Azure AD only auth. |
| aad_only_authentication | string | Azure AD only authentication. |
| ab_test_copy_type | string | Type classification for ab test copy. |
| ab_test_owner | string | Ab test owner. |
| ab_test_tag | string | Ab test tag. |
| ab_test_type | string | Type classification for ab test. |
| account_name | string | Account name. |
| account_owner_puid | string | Account owner puid. |
| acknowledgement_status | string | Status value for acknowledgement. |
| action | string | Action. |
| action_name | string | Action name. |
| activate_database_request_id | string | Activate database request identifier. |
| active_add_file_mosm | bool | Boolean flag indicating whether active add file mosm. |
| active_state_machines | string | Active state machines. |
| actual_database_level_role | string | Actual database level role. |
| actual_server_level_role | string | Actual server level role. |
| actual_state | string | State value for actual. |
| addPageServerCount | long | Add Page Server Count. |
| added_metrics | string | Added metrics. |
| additionalInfo | string | Additional Info. |
| additional_placement_constraints | string | Additional placement constraints. |
| additional_rules | string | Additional rules. |
| adminLoginLength | long | Admin Login Length. |
| administrator_name | string | Administrator name. |
| advisor_auto_execute_value | string | Advisor auto execute value. |
| advisor_name | string | Advisor name. |
| advisor_names | string | Advisor names. |
| advisor_requested_for | string | Advisor requested for. |
| advisor_status | string | Status value for advisor. |
| afec_features | string | Afec features. |
| affinity_tag | string | Affinity tag. |
| aggregate_health_state | string | State value for aggregate health. |
| aggregated_capacity | long | Aggregated capacity. |
| aggregation_function | string | Aggregation function. |
| alias_cache_database_id | string | Alias cache database identifier. |
| aligned_affinity | bool | Boolean flag indicating whether aligned affinity. |
| allocation_forced | bool | Boolean flag indicating whether allocation forced. |
| allow_backup_in_copy_state | bool | Boolean flag indicating whether allow backup in copy state. |
| allow_multiple_per_cycles | string | Allow multiple per cycles. |
| allowed_service_level_objective | string | Allowed service level objective. |
| already_existed | bool | Boolean flag indicating whether already existed. |
| analytics_account_name | string | Analytics account name. |
| api_version | string | Api version. |
| app_key | string | App key. |
| app_type | string | Type classification for app. |
| applicationName | string | Application Name. |
| application_name | string | Application name. |
| application_type_health_state | string | State value for application type health. |
| application_type_name | string | Application type name. |
| application_type_version | string | Application type version. |
| application_uri | string | Application uri. |
| apply_to_existing_cmw_apps | bool | Boolean flag indicating whether apply to existing cmw apps. |
| argument_0 | string | Argument 0. |
| argument_0_name | string | Argument 0 name. |
| argument_1 | string | Argument 1. |
| argument_1_name | string | Argument 1 name. |
| argument_2 | string | Argument 2. |
| argument_2_name | string | Argument 2 name. |
| arm_block_list_property_found | bool | Boolean flag indicating whether arm block list property found. |
| arm_request_uri | string | Arm request uri. |
| arm_request_url | string | Arm request url. |
| assigned_update_slo_mode | string | Assigned update slo mode. |
| async | bool | Boolean flag indicating whether async. |
| async_action_execution_status | string | Status value for async action execution. |
| async_action_input_type | string | Type classification for async action input. |
| async_action_output_type | string | Type classification for async action output. |
| async_action_type | string | Type classification for async action. |
| atm_name | string | Atm name. |
| atm_resource_group | string | Atm resource group. |
| atm_subscription_id | string | Atm subscription identifier. |
| audience_override | string | Audience override. |
| authentication_type | string | Type classification for authentication. |
| authorization_argument | string | Authorization argument. |
| authorization_database_dtu_max | long | Authorization database dtu max. |
| authorization_database_dtu_min | long | Authorization database dtu min. |
| authorization_edition | string | Authorization edition. |
| authorization_elastic_pool_dtu | long | Authorization elastic pool dtu. |
| authorization_elastic_pool_edition | string | Authorization elastic pool edition. |
| authorization_elastic_pool_name | string | Authorization elastic pool name. |
| authorization_elastic_pool_storage_in_megabytes | long | Authorization elastic pool storage in megabytes. |
| authorization_experience_features | string | Authorization experience features. |
| authorization_is_dreamspark | bool | Boolean flag indicating whether authorization dreamspark. |
| authorization_location | string | Authorization location. |
| authorization_max_size_bytes | long | Authorization max size size in bytes. |
| authorization_server_configuration_parameters | string | Authorization server configuration parameters. |
| authorization_server_version | string | Authorization server version. |
| authorization_service_level_objective_id | string | Authorization service level objective identifier. |
| authorization_service_level_objective_name | string | Authorization service level objective name. |
| auto_action_kind | string | Auto action kind. |
| auto_complete_restore | string | Auto complete restore. |
| auto_pause_delay | long | Auto pause delay. |
| automated_cluster_id | string | Automated cluster identifier. |
| automatic_tuning_info | string | Automatic tuning info. |
| autotuning_request | string | Autotuning request. |
| availability_check_result | string | Availability check result. |
| availability_group_id | string | Availability group identifier. |
| availability_zone | string | Availability zone. |
| azureSubscriptionIdForBackupStorageAccount | string | Azure Subscription Id For Backup Storage Account. |
| azure_key_vault_key_name | string | Azure key vault key name. |
| azure_key_vault_uri | string | Azure key vault uri. |
| azure_key_vault_uris | string | Azure key vault uris. |
| azure_request_id | string | Azure request identifier. |
| back_off_period_in_minutes | long | Back off period in minutes. |
| back_off_period_in_seconds | long | Back off period in seconds. |
| back_off_state | float | State value for back off. |
| back_off_until | string | Back off until. |
| backoff_minutes | long | Backoff minutes. |
| backup | bool | Boolean flag indicating whether backup. |
| backupStorageAccountName | string | Backup Storage Account Name. |
| backup_action_status | string | Status value for backup action. |
| backup_action_type | string | Type classification for backup action. |
| backup_billing_enabled | bool | Boolean flag indicating whether backup billing enabled. |
| backup_file_name | string | Backup file name. |
| backup_file_share_quota_mb | long | Backup file share quota mb. |
| backup_lrs_storage_size | long | Backup lrs storage size. |
| backup_name | string | Backup name. |
| backup_ragrs_storage_size | long | Backup ragrs storage size. |
| backup_retention_days | real | Backup retention days. |
| backup_set_id | long | Backup set identifier. |
| backup_storage__account_type | string | Type classification for backup storage account. |
| backup_storage_account_name | string | Backup storage account name. |
| backup_storage_account_type | string | Type classification for backup storage account. |
| backup_storage_container | string | Backup storage container. |
| backup_storage_container_quota_mb | long | Backup storage container quota mb. |
| backup_storage_size | long | Backup storage size. |
| backup_time | string | Backup timestamp associated with the record. |
| backup_type | string | Type classification for backup. |
| backup_zrs_storage_size | long | Backup zrs storage size. |
| base_blob_storage_size_mb | long | Base blob storage size mb. |
| batch_blobs_copied | long | Batch blobs copied. |
| batch_bytes_copied | long | Batch size in bytes copied. |
| batch_total_blobs | long | Batch total blobs. |
| batch_total_bytes | long | Batch total size in bytes. |
| billable_backup_size_mb | long | Billable backup size mb. |
| billable_snapshot_storage_size_mb | long | Billable snapshot storage size mb. |
| billable_xlog_storage_size_mb | long | Billable xlog storage size mb. |
| billing_start_time | string | Billing start time timestamp. |
| blob_count | long | Number of blob. |
| blob_name | string | Blob name. |
| blob_path | string | Blob path. |
| blob_uri | string | Blob uri. |
| blobs_copied | long | Blobs copied. |
| blocked_app_upgrade_start_time | string | Blocked app upgrade start time timestamp. |
| blocked_deloyment_type | string | Type classification for blocked deloyment. |
| blocked_tenant_rings | string | Blocked tenant rings. |
| body | string | Body. |
| buildout_cluster_configuration | string | Buildout cluster configuration. |
| byok_enabled | bool | Boolean flag indicating whether byok enabled. |
| bytes_copied | long | Bytes copied. |
| bytes_per_block | long | Bytes per block. |
| cab_id | long | Cab identifier. |
| cache_instance_name | string | Cache instance name. |
| call_result | long | Call result. |
| caller | string | Caller. |
| caller_address | string | Caller address. |
| caller_file | string | Caller file. |
| caller_function | string | Caller function. |
| caller_ip_address | string | Caller ip address. |
| caller_keys | string | Caller keys. |
| caller_line | long | Caller line. |
| caller_request_id | string | Caller request identifier. |
| caller_state_machine | string | Caller state machine. |
| caller_state_machine_type | string | Type classification for caller state machine. |
| capability_audience | string | Capability audience. |
| capability_policy | string | Capability policy. |
| capability_reason | string | Capability reason. |
| capability_state | string | State value for capability. |
| capacity_limit | long | Capacity limit. |
| capacity_response_assigned_db_role | string | Capacity response assigned database role. |
| capacity_response_code | string | Capacity response code. |
| capacity_response_ip_address_count_change | string | Capacity response ip address count change. |
| capacity_response_node_count_change | string | Capacity response node count change. |
| capacity_response_role_counts | string | Capacity response role counts. |
| capacity_tag | string | Capacity tag. |
| cas_block_list_property_found | bool | Boolean flag indicating whether cas block list property found. |
| catalog_database_name | string | Catalog database name. |
| catalog_server_name | string | Catalog server name. |
| category_name | string | Category name. |
| catlog_database_id | string | Catlog database identifier. |
| certificate_name | string | Certificate name. |
| cf_info_id | string | Cf info identifier. |
| change_version_number | string | Change version number. |
| check_all_replicas | bool | Boolean flag indicating whether check all replicas. |
| check_existing | bool | Boolean flag indicating whether check existing. |
| chosen_certificate_thumbprint | string | Chosen certificate thumbprint. |
| chosen_server_name | string | Chosen server name. |
| cis_job_id | string | Cis job identifier. |
| cleanup_hypothetical | bool | Boolean flag indicating whether cleanup hypothetical. |
| clear_target_fields_only | bool | Boolean flag indicating whether clear target fields only. |
| clientClassificationSource | string | Client Classification Source. |
| client_activity_id | string | Client activity identifier. |
| client_address | string | Client address. |
| client_id | string | Client identifier. |
| client_ip_address | string | Client ip address. |
| client_pid | long | Client pid. |
| client_request_id | string | Client request identifier. |
| client_security_credentials | string | Client security credentials. |
| client_thumbprint | string | Client thumbprint. |
| client_timestamp | datetime | Client timestamp. |
| cluster_address | string | Cluster address. |
| cluster_module_operation_desc | string | Cluster module operation desc. |
| cluster_validation_id | string | Cluster validation identifier. |
| cmdlet_exception | string | Cmdlet exception. |
| cms_backup_container_name | string | Cms backup container name. |
| codePackageName | string | Code Package Name. |
| code_package_version | string | Code package version. |
| codepackage_name | string | Codepackage name. |
| collation | string | Collation. |
| collect_current_thread_id | long | Collect current thread identifier. |
| column | string | Column. |
| columnName | string | Column Name. |
| command | string | Command. |
| common_alias | string | Common alias. |
| component | string | Component. |
| concurrency_token | long | Concurrency token. |
| concurrent_logins | long | Concurrent logins. |
| config_name | string | Config name. |
| config_value | string | Config value. |
| configuration_name | string | Configuration name. |
| configuration_value | string | Configuration value. |
| configurations | string | Configurations. |
| conflict_logging_retention_in_days | long | Conflict logging retention in days. |
| conflict_resolution_policy | string | Conflict resolution policy. |
| connection_id | string | Connection identifier. |
| connection_name | string | Connection name. |
| connection_peer_id | string | Connection peer identifier. |
| connection_string | string | Connection string. |
| connection_string_format | string | Connection string format. |
| connection_type | string | Type classification for connection. |
| connector_name | string | Connector name. |
| connector_type | string | Type classification for connector. |
| consumer | string | Consumer. |
| consumer_id | string | Consumer identifier. |
| contained_authentication_time_ms | long | Contained authentication time ms in milliseconds. |
| container_count | long | Number of container. |
| container_name | string | Container name. |
| container_or_share_name | string | Container or share name. |
| container_type | string | Type classification for container. |
| containment_state | string | State value for containment. |
| content_length | long | Content length. |
| context_info | string | Context info. |
| context_instance_name | string | Context instance name. |
| continuation_token | string | Continuation token. |
| control_ring_address | string | Control ring address. |
| control_ring_name | string | Control ring name. |
| copy_batch_id | string | Copy batch identifier. |
| copy_batch_seq_no | long | Copy batch seq no. |
| copy_duration | string | Copy duration. |
| copy_end_time | datetime | Copy end time timestamp. |
| copy_operation_type | string | Type classification for copy operation. |
| copy_start_time | datetime | Copy start time timestamp. |
| correlation_id | string | Correlation identifier used across components. |
| correlation_request_id | string | Correlation request identifier. |
| cosmosdb_account_name | string | Cosmosdb account name. |
| cosmosdb_account_subscription_id | string | Cosmosdb account subscription identifier. |
| count | long | Number of count. |
| count_limit | long | Number of count limit. |
| count_seps | long | Number of count seps. |
| create_mode | string | Create mode. |
| create_time | datetime | Creation timestamp. |
| created | string | Created. |
| creation_passed | bool | Boolean flag indicating whether creation passed. |
| current_backup_retention_days | real | Current backup retention days. |
| current_capacity | long | Current capacity. |
| current_db_node_count | long | Number of current database node. |
| current_priority | string | Current priority. |
| current_progress | string | Current progress. |
| current_resource_group | string | Current resource group. |
| current_retry_count | string | Number of current retry. |
| current_server_version | string | Current server version. |
| current_state | string | State value for current. |
| current_storage_size_bytes | long | Current storage size size in bytes. |
| current_ud | string | Current ud. |
| current_version | long | Current version. |
| currently_impacted_nodes | string | Currently impacted nodes. |
| customer_error_message | string | Customer error message. |
| customer_flighting_tag | string | Customer flighting tag. |
| customer_subscription_id | string | Customer subscription identifier. |
| customer_time_zone | string | Customer time zone. |
| cycles | string | Cycles. |
| da_throttling_threshold | long | Da throttling threshold. |
| data | string | Data. |
| data_exfiltration_allowed_fqdn_list | string | Data exfiltration allowed fqdn list. |
| data_exfiltration_settings | string | Data exfiltration settings. |
| data_file_operation_request_id | string | Data file operation request identifier. |
| data_retention | string | Data retention. |
| databaseName | string | Database Name. |
| database_charset | string | Database charset. |
| database_collation | string | Database collation. |
| database_create_time | string | Database create time timestamp. |
| database_dtu_max | long | Database dtu max. |
| database_dtu_min | long | Database dtu min. |
| database_file_blob_count_current | long | Database file blob count current. |
| database_file_blob_count_to_reserve | long | Database file blob count to reserve. |
| database_firewall_rules_time_ms | long | Database firewall rules time ms in milliseconds. |
| database_id | string | Database identifier. |
| database_max_size_in_bytes | long | Database max size in size in bytes. |
| database_name | string | Database name. |
| database_operation_request_id | string | Database operation request identifier. |
| database_storage_size_mb | long | Database storage size mb. |
| database_target_slo | string | Database target slo. |
| database_type | string | Type classification for database. |
| databasesList | string | Databases List. |
| dates | string | Dates. |
| db_file_growth | string | Database file growth. |
| db_file_max_size | string | Database file max size. |
| db_file_name | string | Database file name. |
| db_name | string | Database name. |
| deactivated_block_blobs_size_bytes | long | Deactivated block blobs size size in bytes. |
| deactivated_database_size_bytes | long | Deactivated database size size in bytes. |
| deactivated_geosnapshot_size_bytes | long | Deactivated geosnapshot size size in bytes. |
| deactivated_snapshot_size_bytes | long | Deactivated snapshot size size in bytes. |
| deactivation_execution_mode | string | Deactivation execution mode. |
| default_move_cost | string | Default move cost. |
| default_value | long | Default value. |
| deployment_configuration | string | Deployment configuration. |
| deployment_id | string | Deployment identifier. |
| deployment_message | string | Deployment message. |
| deployment_name | string | Deployment name. |
| deployment_pinning_info_id | string | Deployment pinning info identifier. |
| deployment_script | string | Deployment script. |
| description | string | Description. |
| desired_update_slo_mode | string | Desired update slo mode. |
| destaged_blob_size_in_bytes | long | Destaged blob size in size in bytes. |
| details | string | Details. |
| dev_scenario_description | string | Dev scenario description. |
| dev_scenario_type | string | Type classification for dev scenario. |
| deviceCount | long | Device Count. |
| devops_access_level | string | Devops access level. |
| devops_action | string | Devops action. |
| devops_database_name | string | Devops database name. |
| devops_expiration_time | string | Devops expiration time timestamp. |
| devops_login | string | Devops login. |
| devops_oid | string | Devops oid. |
| devops_server_name | string | Devops server name. |
| devops_sql_instance_name | string | Devops SQL instance name. |
| devops_sql_physical_database_id | string | Devops SQL physical database identifier. |
| devops_tenant_id | string | Devops tenant identifier. |
| diff_backup_count | long | Number of diff backup. |
| diff_backup_cumulative_size | long | Diff backup cumulative size. |
| differentialSellableRatio | long | Differential Sellable Ratio. |
| directory_name | string | Directory name. |
| directory_path | string | Directory path. |
| disable_trace_flags | string | Disable trace flags. |
| disaster_recovery_configuration_operation_request_id | string | Disaster recovery configuration operation request identifier. |
| distance_in_bytes | long | Distance in size in bytes. |
| distributed_availability_group_name | string | Distributed availability group name. |
| dngId | string | Dng Id. |
| dng_id | string | Dng identifier. |
| dnsName | string | Dns Name. |
| dnsRecordId | string | Dns Record Id. |
| dnsRecordType | string | Dns Record Type. |
| dns_name | string | Dns name. |
| dns_prefix | string | Dns prefix. |
| dns_zone | string | Dns zone. |
| dosguard_check_time_ms | long | Dosguard check time ms in milliseconds. |
| dqp_vcore_count | long | Number of dqp vCore. |
| driver_name | string | Driver name. |
| driver_version | long | Driver version. |
| driver_version_minor | long | Driver version minor. |
| drop_retention | string | Drop retention. |
| dropped_time | string | Dropped time timestamp. |
| dss_error_message | string | Dss error message. |
| dtu | long | Dtu. |
| duration | string | Duration. |
| duration_of_window | string | Duration of window. |
| dw_maintenance_windows | string | Billing warehouse maintenance windows. |
| dw_query_id | string | Billing warehouse query identifier. |
| edition | string | Edition. |
| effective_slo_id | string | Effective slo identifier. |
| elapsedTime | string | Elapsed Time. |
| elapsed_time | string | Elapsed duration for the operation. |
| elapsed_time_days | real | Elapsed time days. |
| elapsed_time_in_batch_milliseconds | real | Elapsed time in batch in milliseconds. |
| elapsed_time_in_copy_operation_seconds | real | Elapsed time in copy operation seconds. |
| elapsed_time_in_milliseconds | real | Elapsed time in in milliseconds. |
| elapsed_time_milliseconds | real | Elapsed duration in milliseconds. |
| elasped_time | string | Elasped time timestamp. |
| elastic_pool_dtu | long | Elastic pool dtu. |
| elastic_pool_edition | string | Elastic pool edition. |
| elastic_pool_estimate_name | string | Elastic pool estimate name. |
| elastic_pool_id | string | Elastic pool identifier. |
| elastic_pool_name | string | Elastic pool name. |
| elastic_pool_storage_in_megabytes | long | Elastic pool storage in megabytes. |
| elastic_server_id | string | Elastic server identifier. |
| elastic_server_instance_name | string | Elastic server instance name. |
| elastic_server_name | string | Elastic server name. |
| elastic_server_source_name | string | Elastic server source name. |
| elastic_server_source_resource_group | string | Elastic server source resource group. |
| elastic_server_target_name | string | Elastic server target name. |
| elastic_server_type | string | Type classification for elastic server. |
| elasticserver_id | string | Elasticserver identifier. |
| emailContent | string | Email Content. |
| emailSender | string | Email Sender. |
| email_batch_id | string | Email batch identifier. |
| email_batch_status | string | Status value for email batch. |
| enable | string | Enable. |
| enable_conflict_logging | bool | Boolean flag indicating whether enable conflict logging. |
| enable_delta_health_evaluation | string | Enable delta health evaluation. |
| enable_infrastructure_encryption | bool | Boolean flag indicating whether enable infrastructure encryption. |
| enable_ssl_enforcement | string | Enable ssl enforcement. |
| enable_trace_flags | string | Enable trace flags. |
| enabled | bool | Boolean flag indicating whether enabled. |
| encryption | string | Encryption. |
| encryption_protector_type | string | Type classification for encryption protector. |
| end_ip_address | string | End ip address. |
| end_time | string | End timestamp. |
| endpoint | string | Endpoint. |
| endpoint_name | string | Endpoint name. |
| endpoint_type | long | Type classification for endpoint. |
| endpoints | string | Endpoints. |
| enqueue_time_ms | long | Enqueue time ms in milliseconds. |
| enrollment_account_id | string | Enrollment account identifier. |
| entities_condition_type | string | Type classification for entities condition. |
| entitled_subscription | string | Entitled subscription. |
| environment | string | Environment. |
| error | long | Error text captured for the event or operation. |
| errorCode | long | Error Code. |
| error_classification | string | Error classification. |
| error_code | string | Numeric error code for the failure or event. |
| error_message | string | Error message. |
| error_message_format | string | Error message format. |
| error_message_resourcename | string | Error message resourcename. |
| error_message_scrubbed | string | Error message scrubbed. |
| error_message_systemmetadata | string | Error message systemmetadata. |
| error_number | string | SQL or platform error number. |
| error_severity | long | Error severity. |
| estimated_restored_bsn_progress | long | Estimated restored bsn progress. |
| estimated_restored_lsn_hex | string | Estimated restored lsn hex. |
| eta_in_days | long | Eta in days. |
| event | string | Event name emitted by the component. |
| eventToFire | string | Event To Fire. |
| event_name | string | Event name. |
| event_time | string | Event time timestamp. |
| event_type | string | Type classification for event. |
| exception | string | Exception. |
| exception_format | string | Exception format. |
| exception_message | string | Exception message. |
| exception_message_scrubbed | string | Exception message scrubbed. |
| exception_resource_name | string | Exception resource name. |
| exception_scrubbed | string | Exception scrubbed. |
| exception_type | string | Type classification for exception. |
| exclude_current_sql_instance | bool | Boolean flag indicating whether exclude current SQL instance. |
| excluded_instance | string | Excluded instance. |
| exec_classifier_ms | long | Exec classifier ms in milliseconds. |
| executeEventSessionCommandActionHelperSpec | string | Execute Event Session Command Action Helper Spec. |
| executed_in_container | bool | Boolean flag indicating whether executed in container. |
| execution_time | string | Execution time timestamp. |
| execution_type | string | Type classification for execution. |
| exipry_date | datetime | Exipry date. |
| expected_current_state | string | State value for expected current. |
| expected_database_level_role | string | Expected database level role. |
| expected_diff_backup_count | long | Number of expected diff backup. |
| expected_full_backup_count | long | Number of expected full backup. |
| expected_number_of_migrations_executed | long | Expected number of migrations executed. |
| expected_server_level_role | string | Expected server level role. |
| experience_audience_count | long | Number of experience audience. |
| experience_audience_definition | string | Experience audience definition. |
| experience_audience_is_enabled | bool | Boolean flag indicating whether experience audience enabled. |
| experience_audience_layer | long | Experience audience layer. |
| experience_audience_name | string | Experience audience name. |
| experience_policy_is_enabled | bool | Boolean flag indicating whether experience policy enabled. |
| experience_policy_is_singleton_available | bool | Boolean flag indicating whether experience policy singleton available. |
| experience_policy_item_count | long | Number of experience policy item. |
| experience_policy_layer | long | Experience policy layer. |
| experience_policy_name | string | Experience policy name. |
| experience_policy_scope_count | long | Number of experience policy scope. |
| experience_region | string | Experience region. |
| expiry_date | datetime | Expiry date. |
| external_admin_login_sid | string | External admin login sid. |
| external_admin_principal_type | long | Type classification for external admin principal. |
| external_admin_type | string | Type classification for external admin. |
| external_governance_policy_authorization | string | External governance policy authorization. |
| external_sid | string | External sid. |
| extraParams | string | Extra Params. |
| extra_info | string | Extra info. |
| fabricApplicationUri | string | Fabric Application Uri. |
| fabricClusterName | string | Fabric Cluster Name. |
| fabric_application_uri | string | Fabric application uri. |
| fabric_cluster_dns_name | string | Fabric cluster dns name. |
| fabric_cluster_name | string | Fabric cluster name. |
| fabric_cluster_one | string | Fabric cluster one. |
| fabric_cluster_two | string | Fabric cluster two. |
| fabric_controller | string | Fabric controller. |
| fabric_name_state_machine_log_message | string | Fabric name state machine log message. |
| fabric_name_uri | string | Fabric name uri. |
| fabric_property_name | string | Fabric property name. |
| fabric_replicas | string | Fabric replicas. |
| fabric_service_uri | string | Fabric service uri. |
| failover_alias | string | Failover alias. |
| failover_configuration_id | string | Failover configuration identifier. |
| failover_grace_period_in_minutes | string | Failover grace period in minutes. |
| failover_group_id | string | Failover group identifier. |
| failover_group_name | string | Failover group name. |
| failover_policy | string | Failover policy. |
| failover_with_data_loss_grace_period_in_minutes | string | Failover with data loss grace period in minutes. |
| failure_action | string | Failure action. |
| failure_state | string | State value for failure. |
| fe_vcore_count | long | Number of fe vCore. |
| feature_name | string | Feature name. |
| feature_namespace | string | Feature namespace. |
| feature_value | string | Feature value. |
| fedauth_adal_workflow | int | Fedauth adal workflow. |
| fedauth_context_build_time_ms | long | Fedauth context build time ms in milliseconds. |
| fedauth_fetch_signingkey_refresh_time_ms | long | Fedauth fetch signingkey refresh time ms in milliseconds. |
| fedauth_group_expansion_time_ms | long | Fedauth group expansion time ms in milliseconds. |
| fedauth_jwt_token_parsing_time_ms | long | Fedauth jwt token parsing time ms in milliseconds. |
| fedauth_library_type | int | Type classification for fedauth library. |
| fedauth_signature_validation_time_ms | long | Fedauth signature validation time ms in milliseconds. |
| fedauth_token_process_time_ms | long | Fedauth token process time ms in milliseconds. |
| fedauth_token_wait_time_ms | long | Fedauth token wait time ms in milliseconds. |
| file | string | File. |
| fileContent | string | File Content. |
| fileCount | long | File Count. |
| file_id | long | File identifier. |
| file_path | string | File path. |
| file_share_name | string | File share name. |
| file_share_path | string | File share path. |
| file_share_quota_mb | long | File share quota mb. |
| files_count | long | Number of files. |
| filter_id | long | Filter identifier. |
| filter_uri | string | Filter uri. |
| filtered_by_capacity_tag_count | long | Number of filtered by capacity tag. |
| find_login_ms | long | Find login ms in milliseconds. |
| firewall_id | string | Firewall identifier. |
| firewall_rule_name | string | Firewall rule name. |
| firewall_rules | string | Firewall rules. |
| firstBackupTime | datetime | First Backup Time. |
| first_destage_block_timestamp_for_last_destage_blob | datetime | First destage block timestamp for last destage blob. |
| first_vlf_id | long | First vlf identifier. |
| force | string | Force. |
| force_refresh_status | long | Status value for force refresh. |
| force_restart | string | Force restart. |
| forced_action | bool | Boolean flag indicating whether forced action. |
| forced_source_ring | string | Forced source ring. |
| forcenewapp | bool | Boolean flag indicating whether forcenewapp. |
| fqdn | string | Fqdn. |
| free_database_days_left | long | Free database days left. |
| frequency | string | Frequency. |
| freshness_number | string | Freshness number. |
| friendly_name | string | Friendly name. |
| fsm_context_incarnation | long | Fsm context incarnation. |
| fsm_error_message | string | Fsm error message. |
| fsm_event | string | Fsm event. |
| fsm_id | string | Fsm identifier. |
| fsm_instance_id | string | Fsm instance identifier. |
| fsm_operation_parameters | string | Fsm operation parameters. |
| fsm_operation_result | string | Fsm operation result. |
| fsm_request_id | string | Fsm request identifier. |
| fsm_table_name | string | Fsm table name. |
| fsm_types | string | Fsm types. |
| fsm_version | long | Fsm version. |
| full_backup_count | long | Number of full backup. |
| full_backup_cumulative_size | long | Full backup cumulative size. |
| full_backup_times | string | Full backup times. |
| fuse_event_name | string | Fuse event name. |
| gateway_slice_id | string | Gateway slice identifier. |
| gateway_slice_type | string | Type classification for gateway slice. |
| gc_memory_delta | real | Gc memory delta. |
| grace_distance_in_bytes | long | Grace distance in size in bytes. |
| grg_name | string | Grg name. |
| group_name | string | Group name. |
| handler_id | long | Handler identifier. |
| hardware_family | string | Hardware family. |
| hardware_generation | string | Hardware generation. |
| has_external_admin | bool | Boolean flag indicating whether has external admin. |
| has_legal_hold | bool | Boolean flag indicating whether has legal hold. |
| has_permissions | bool | Boolean flag indicating whether has permissions. |
| has_placement_preference_tag | bool | Boolean flag indicating whether has placement preference tag. |
| health_check_retry_timeout | string | Health check retry timeout. |
| health_check_stable_duration | string | Health check stable duration. |
| health_check_wait_duration | string | Health check wait duration. |
| health_state | string | State value for health. |
| history | string | History. |
| hk_file_group_id | long | Hk file group identifier. |
| hosted_service_name | string | Hosted service name. |
| hosted_service_subscription_id | string | Hosted service subscription identifier. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| http_method | string | Http method. |
| http_verb | string | Http verb. |
| hubLogicalDatabaseName | string | Hub Logical Database Name. |
| hubLogicalServerName | string | Hub Logical Server Name. |
| hub_database_name | string | Hub database name. |
| hub_server_name | string | Hub server name. |
| hub_state | string | State value for hub. |
| hubdb_logical_database_name | string | Hubdb logical database name. |
| hubdb_logical_server_name | string | Hubdb logical server name. |
| idempotency_key | string | Idempotency key. |
| identity_name | string | Identity name. |
| identity_principal_id | string | Identity principal identifier. |
| identity_tenant_id | string | Identity tenant identifier. |
| identity_url | string | Identity url. |
| ignore_blacklist_flag | bool | Boolean flag indicating whether ignore blacklist flag. |
| ignore_constraints | bool | Boolean flag indicating whether ignore constraints. |
| ignore_for_Anomaly | bool | Boolean flag indicating whether ignore for Anomaly. |
| impacted_node | string | Impacted node. |
| impacted_role_instances | string | Impacted role instances. |
| in_workflow | bool | Boolean flag indicating whether in workflow. |
| incidentId | long | Incident Id. |
| index | long | Index. |
| index_id | long | Index identifier. |
| index_name | string | Index name. |
| index_request | string | Index request. |
| index_request_key | string | Index request key. |
| informationType | string | Information Type. |
| informationTypeId | string | Information Type Id. |
| infra_weight | long | Infra weight. |
| initial_collation | string | Initial collation. |
| initial_hardware_family | string | Initial hardware family. |
| initial_is_mi_link_disaster_recovery_only | string | Initial is MI link disaster recovery only. |
| initial_maintenance_policy_id | string | Initial maintenance policy identifier. |
| initial_public_ip | bool | Boolean flag indicating whether initial public ip. |
| initial_service_level_objective_name | string | Initial service level objective name. |
| initial_sql_server_licence | string | Initial SQL server licence. |
| initial_storage_iops | long | Initial storage IOPS. |
| initial_storage_size_in_gb | long | Initial storage size in gb. |
| initial_storage_throughput_mbps | long | Initial storage throughput mbps. |
| initial_subnet_id | string | Initial subnet identifier. |
| initial_total_memory_mb | long | Initial total memory mb. |
| initial_vcore_count | long | Number of initial vCore. |
| instance | string | Instance. |
| instance_affinity_tag | string | Instance affinity tag. |
| instance_capacities | string | Instance capacities. |
| instance_id | string | Instance identifier. |
| instance_name | string | Instance name. |
| instance_partner_configuration | string | Instance partner configuration. |
| instance_pool_name | string | Instance pool name. |
| instance_tenant_ring_name | string | Instance tenant ring name. |
| instance_type | string | Type classification for instance. |
| intent_policy | string | Intent policy. |
| intent_policy_check_id | string | Intent policy check identifier. |
| intent_policy_config | string | Intent policy config. |
| intent_policy_resource_id | string | Intent policy resource identifier. |
| intent_policy_value | string | Intent policy value. |
| internal_load_balancer_ip_address | string | Internal load balancer ip address. |
| internal_server_dns_name | string | Internal server dns name. |
| internal_service_level_objective_id | string | Internal service level objective identifier. |
| internal_service_level_objective_name | string | Internal service level objective name. |
| internal_settings | string | Internal settings. |
| interval_in_milliseconds | long | Interval in in milliseconds. |
| interval_length_minutes | long | Interval length minutes. |
| interval_type | string | Type classification for interval. |
| intial_edition | string | Intial edition. |
| invalid_certificate_thumbprint | string | Invalid certificate thumbprint. |
| invalid_result | bool | Boolean flag indicating whether invalid result. |
| invocation_elapsed_time_milliseconds | real | Invocation elapsed time in milliseconds. |
| isDatabaseCopy | bool | Boolean flag indicating whether Database Copy. |
| isOverrideFile | bool | Boolean flag indicating whether Override File. |
| isStateless | bool | Boolean flag indicating whether Stateless. |
| isViaTSql | bool | Boolean flag indicating whether Via TSql. |
| is_ab_test | bool | Boolean flag indicating whether ab test. |
| is_active_in_region | string | Boolean flag indicating whether active in region. |
| is_adding | bool | Boolean flag indicating whether adding. |
| is_anonymous | bool | Boolean flag indicating whether anonymous. |
| is_aprc_force | bool | Boolean flag indicating whether aprc force. |
| is_authenticated | bool | Boolean flag indicating whether authenticated. |
| is_automitigation_enabled | bool | Boolean flag indicating whether automitigation enabled. |
| is_best_effort | bool | Boolean flag indicating whether best effort. |
| is_billable | bool | Boolean flag indicating whether billable. |
| is_blocked | bool | Boolean flag indicating whether blocked. |
| is_cached_result | bool | Boolean flag indicating whether cached result. |
| is_chosen | bool | Boolean flag indicating whether chosen. |
| is_cmw_ring | bool | Boolean flag indicating whether cmw ring. |
| is_contained_user | bool | Boolean flag indicating whether contained user. |
| is_create | bool | Boolean flag indicating whether create. |
| is_cross_server_restore | bool | Boolean flag indicating whether cross server restore. |
| is_currently_in_teardown | bool | Boolean flag indicating whether currently in teardown. |
| is_customer_initiated | bool | Boolean flag indicating whether customer initiated. |
| is_duplicate_request | bool | Boolean flag indicating whether duplicate request. |
| is_duplicated | bool | Boolean flag indicating whether duplicated. |
| is_enabled | bool | Boolean flag indicating whether enabled. |
| is_external_authentication_only | bool | Boolean flag indicating whether external authentication only. |
| is_failoverpartner_token_returned | bool | Boolean flag indicating whether failoverpartner token returned. |
| is_force | bool | Boolean flag indicating whether force. |
| is_forced | string | Boolean flag indicating whether forced. |
| is_forced_failover | bool | Boolean flag indicating whether forced failover. |
| is_free_database_supported | bool | Boolean flag indicating whether free database supported. |
| is_geo_secondary_disaster_recovery_only | string | Boolean flag indicating whether geo secondary disaster recovery only. |
| is_in_place_update_slo | bool | Boolean flag indicating whether in place update slo. |
| is_increase_max_size | string | Boolean flag indicating whether increase max size. |
| is_independent | bool | Boolean flag indicating whether independent. |
| is_instance_authorization | bool | Boolean flag indicating whether instance authorization. |
| is_internal_backup_retention | bool | Boolean flag indicating whether internal backup retention. |
| is_internal_request | bool | Boolean flag indicating whether internal request. |
| is_ipv6_enabled | bool | Boolean flag indicating whether ipv6 enabled. |
| is_logical_resume | bool | Boolean flag indicating whether logical resume. |
| is_maintenance_notification_enabled | bool | Boolean flag indicating whether maintenance notification enabled. |
| is_managed_instance | bool | Boolean flag indicating whether managed instance. |
| is_manual | bool | Boolean flag indicating whether manual. |
| is_mars | bool | Boolean flag indicating whether mars. |
| is_max_size_bytes_updated | bool | Is max size size in bytes updated. |
| is_mfa | bool | Boolean flag indicating whether mfa. |
| is_mi_link_disaster_recovery_only | string | Boolean flag indicating whether MI link disaster recovery only. |
| is_nsp_claim_present | bool | Boolean flag indicating whether nsp claim present. |
| is_paasV2 | bool | Boolean flag indicating whether paas V2. |
| is_paas_v2 | bool | Boolean flag indicating whether paas v2. |
| is_peer_activity_id_null | bool | Boolean flag indicating whether peer activity id null. |
| is_physical_db_deactivated | bool | Boolean flag indicating whether physical database deactivated. |
| is_plan_forcing | bool | Boolean flag indicating whether plan forcing. |
| is_public_endpoint_enabled | string | Boolean flag indicating whether public endpoint enabled. |
| is_rdfe_proxy_traffic_enabled | string | Boolean flag indicating whether rdfe proxy traffic enabled. |
| is_reattach_update_slo | bool | Boolean flag indicating whether reattach update slo. |
| is_relogin | bool | Boolean flag indicating whether relogin. |
| is_replace_action | bool | Boolean flag indicating whether replace action. |
| is_replay_connection | bool | Boolean flag indicating whether replay connection. |
| is_same_account_restore | string | Boolean flag indicating whether same account restore. |
| is_same_region_restore | bool | Boolean flag indicating whether same region restore. |
| is_seeding_update_slo | bool | Boolean flag indicating whether seeding update slo. |
| is_stable_state | bool | Boolean flag indicating whether stable state. |
| is_storage_target_path_formatted | bool | Boolean flag indicating whether storage target path formatted. |
| is_success | bool | Boolean flag indicating whether success. |
| is_successful | bool | Boolean flag indicating whether successful. |
| is_test | string | Boolean flag indicating whether test. |
| is_unhandled_fsm_user_exception | bool | Boolean flag indicating whether unhandled fsm user exception. |
| is_user_error | bool | Boolean flag indicating whether user error. |
| is_vbs_enabled | bool | Boolean flag indicating whether vbs enabled. |
| is_vnet_address | bool | Boolean flag indicating whether vnet address. |
| is_vnet_private_access_address | bool | Boolean flag indicating whether vnet private access address. |
| is_whitelisted | bool | Boolean flag indicating whether whitelisted. |
| issue_details | string | Issue details. |
| issuer_name | string | Issuer name. |
| jdbc_connection_url | string | Jdbc connection url. |
| job_account_id | string | Job account identifier. |
| job_account_name | string | Job account name. |
| job_agent_name | string | Job agent name. |
| job_id | string | Job identifier. |
| job_start_time | string | Job start time timestamp. |
| job_type | string | Type classification for job. |
| justification | string | Justification. |
| key_count | long | Number of key. |
| key_name | string | Key name. |
| key_type | string | Type classification for key. |
| key_uri | string | Key uri. |
| key_vault_key_info | string | Key vault key info. |
| key_vault_region | string | Key vault region. |
| keys | string | Keys. |
| labelId | string | Label Id. |
| labelName | string | Label Name. |
| lastBackupName | string | Last Backup Name. |
| last_backup_name | string | Last backup name. |
| last_backup_storage_size_refresh_time | string | Last backup storage size refresh time timestamp. |
| last_exception | string | Last exception. |
| last_multiaz_resource_drop_time | string | Last multiaz resource drop time timestamp. |
| last_password_update_time | datetime | Last password update time timestamp. |
| last_rollover_time | datetime | Last rollover time timestamp. |
| leaked_files_in_container | bool | Boolean flag indicating whether leaked files in container. |
| level | string | Level. |
| license_type | string | Type classification for license. |
| link_name | string | Link name. |
| link_type | string | Type classification for link. |
| list | string | List. |
| local_replica_id | string | Local replica identifier. |
| local_replication_role | string | Local replication role. |
| local_ring_dns_name | string | Local ring dns name. |
| local_role | string | Local role. |
| location | string | Location. |
| location_header | string | Location header. |
| location_name | string | Location name. |
| location_placement_id | string | Location placement identifier. |
| log_backup_cumulative_size | long | Log backup cumulative size. |
| logicalDatabaseId | string | Logical Database Id. |
| logicalDatabaseName | string | Logical Database Name. |
| logical_database | string | Logical database. |
| logical_database_collation | string | Logical database collation. |
| logical_database_dropped_time | string | Logical database dropped time timestamp. |
| logical_database_edition | string | Logical database edition. |
| logical_database_id | string | Logical database identifier. |
| logical_database_ids | string | Logical database ids. |
| logical_database_max_size | string | Logical database max size. |
| logical_database_name | string | Logical database name. |
| logical_database_service_level_objective | string | Logical database service level objective. |
| logical_database_service_level_objective_id | string | Logical database service level objective identifier. |
| logical_database_slo | string | Logical database slo. |
| logical_database_tde | string | Logical database tde. |
| logical_databse_name | string | Logical databse name. |
| logical_master_db_id | string | Logical master database identifier. |
| logical_resource_pool_id | string | Logical resource pool identifier. |
| logical_resource_pool_name | string | Logical resource pool name. |
| logical_resource_pool_resource_group_name | string | Logical resource pool resource group name. |
| logical_server | string | Logical server. |
| logical_server_communication_name | string | Logical server communication name. |
| logical_server_dropped_time | datetime | Logical server dropped time timestamp. |
| logical_server_encryption_keys_operation_type | string | Type classification for logical server encryption keys operation. |
| logical_server_encryption_protector_operation_type | string | Type classification for logical server encryption protector operation. |
| logical_server_id | string | Logical server identifier. |
| logical_server_operation_type | string | Type classification for logical server operation. |
| logical_server_state | string | State value for logical server. |
| login_correlation_hash | string | Login correlation hash. |
| login_error_code | long | Login error code. |
| login_flags | long | Login flags. |
| login_time_ms | long | Login time ms in milliseconds. |
| logon_triggers_time_ms | long | Logon triggers time ms in milliseconds. |
| long_transaction_duration_threshold | string | Long transaction duration threshold. |
| long_transaction_log_in_bytes_threshold | string | Long transaction log in size in bytes threshold. |
| lrg_name | string | Lrg name. |
| ltr_backup_time | string | LTR backup time timestamp. |
| lz_last_active_vlf_id | long | Lz last active vlf identifier. |
| maint_config_internal_id | string | Maint config internal identifier. |
| maintenance_configuration | string | Maintenance configuration. |
| maintenance_cycle_end_time | string | Maintenance cycle end time timestamp. |
| maintenance_cycle_id | string | Maintenance cycle identifier. |
| maintenance_cycle_start_time | string | Maintenance cycle start time timestamp. |
| maintenance_end_time | string | Maintenance end time timestamp. |
| maintenance_policy_id | string | Maintenance policy identifier. |
| maintenance_schedule_id | string | Maintenance schedule identifier. |
| maintenance_start_time | string | Maintenance start time timestamp. |
| managedDatabaseId | string | Managed Database Id. |
| managed_database_id | string | Managed database identifier. |
| managed_database_name | string | Managed database name. |
| managed_disk_subscription_id | string | Managed disk subscription identifier. |
| managed_disk_user_identity_name | string | Managed disk user identity name. |
| managed_instance_read_scale_units | string | Managed instance read scale units. |
| managed_restore_id | string | Managed restore identifier. |
| managed_server_id | string | Managed Instance identifier. |
| managed_server_name | string | Managed server name. |
| managed_server_private_cluster_id | string | Managed server private cluster identifier. |
| management_operation_id | string | Management operation identifier. |
| management_operation_ids | string | Management operation ids. |
| management_operation_name | string | Management operation name. |
| management_operation_request_id | string | Management operation request identifier. |
| manifestName | string | Manifest Name. |
| mapping_file | string | Mapping file. |
| max_cpu_percentage_lookback_time | string | Max CPU percentageage lookback time timestamp. |
| max_cpu_percentage_threshold | string | Maximum CPU percentageage threshold. |
| max_evacuate_time | string | Max evacuate time timestamp. |
| max_latency | long | Maximum latency. |
| max_log_size | long | Maximum log size. |
| max_log_write_rate_percentage_lookback_time | string | Max log write rate percentageage lookback time timestamp. |
| max_log_write_rate_percentage_threshold | string | Maximum log write rate percentageage threshold. |
| max_retries_count | string | Number of max retries. |
| max_retry_count | long | Number of max retry. |
| max_size_bytes | long | Max size size in bytes. |
| max_storage_size_bytes | long | Max storage size size in bytes. |
| max_upgrading_capacity_percent | string | Maximum upgrading capacity percentage. |
| maximum_number_of_migrations_executing | long | Maximum number of migrations executing. |
| member_database_name | string | Member database name. |
| member_database_server_name | string | Member database server name. |
| member_database_type | string | Type classification for member database. |
| member_state | string | State value for member. |
| message | string | Human-readable message text. |
| message_format | string | Message format. |
| message_resourcename | string | Message resourcename. |
| message_scrubbed | string | Message scrubbed. |
| message_scrubbed_resource_name | string | Message scrubbed resource name. |
| message_scrubbed_system_metadata | string | Message scrubbed system metadata. |
| message_systemmetadata | string | Message systemmetadata. |
| metadata_store_cluster_dns_location | string | Metadata store cluster dns location. |
| metadata_store_service_alias | string | Metadata store service alias. |
| method_name | string | Method name. |
| metric_name | string | Metric name. |
| metric_names | string | Metric names. |
| metric_vector | string | Metric vector. |
| metric_weight | string | Metric weight. |
| metrics_delay | long | Metrics delay. |
| metrics_publishing_skipped | bool | Boolean flag indicating whether metrics publishing skipped. |
| migration_engine_id | string | Migration engine identifier. |
| migration_id | string | Migration identifier. |
| migration_operation | string | Migration operation. |
| migration_scenario_type | string | Type classification for migration scenario. |
| migration_source_cluster_name | string | Migration source cluster name. |
| min_capacity | real | Minimum capacity. |
| min_cycles | string | Minimum cycles. |
| min_latency | long | Minimum latency. |
| min_node_count_for_sla | string | Minimum node count for sla. |
| min_replica_count | long | Number of min replica. |
| min_success_rate_percentage | long | Min success rate pe percentage. |
| minimal_tls_version | string | Minimal tls version. |
| minutes | long | Minutes. |
| mismatched_instances | string | Mismatched instances. |
| modified | bool | Boolean flag indicating whether modified. |
| move_operation_agent | string | Move operation agent. |
| movementId | string | Movement Id. |
| multi_channel | bool | Boolean flag indicating whether multi channel. |
| name | string | Object or resource name. |
| namespace_uri | string | Namespace uri. |
| netread_time_ms | long | Netread time ms in milliseconds. |
| network_container_id | string | Network container identifier. |
| network_id | string | Network identifier. |
| network_resource_id | string | Network resource identifier. |
| netwrite_time_ms | long | Netwrite time ms in milliseconds. |
| new_capacity | long | New capacity. |
| new_encryption | bool | Boolean flag indicating whether new encryption. |
| new_failover_state | string | State value for new failover. |
| new_file_service_properties | string | New file service properties. |
| new_number_of_nodes | string | New number of nodes. |
| new_primary_database_id | string | New primary database identifier. |
| new_primary_database_name | string | New primary database name. |
| new_primary_key_hash | string | New primary key hash. |
| new_primary_server_name | string | New primary server name. |
| new_qds_value | string | New Query Store value. |
| new_resource_pool_name | string | New resource pool name. |
| new_role | string | New role. |
| new_secondary_key_hash | string | New secondary key hash. |
| new_server_name | string | New server name. |
| new_state | string | State value for new. |
| new_storage_account_type | string | Type classification for new storage account. |
| new_tr_cms_state | string | State value for new tr cms. |
| new_value | string | New value. |
| new_version | long | New version. |
| next_action | string | Next action. |
| next_window_start_time | string | Next window start time timestamp. |
| nip_has_difference | bool | Boolean flag indicating whether nip has difference. |
| no_capacity_cause | string | No capacity cause. |
| nodeId | string | Node Id. |
| node_id | string | Node identifier. |
| node_name_filter | string | Node name filter. |
| notification_id | string | Notification identifier. |
| notification_scope | string | Notification scope. |
| notification_type | string | Type classification for notification. |
| nrp_request | string | Nrp request. |
| nrp_response_body | string | Nrp response body. |
| num_deployment_variables_garbage_collected | long | Num deployment variables garbage collected. |
| num_files_deleted | long | Num files deleted. |
| number_of_accounts | long | Number of accounts. |
| number_of_bacend_nodes | long | Number of bacend nodes. |
| number_of_backend_nodes | long | Number of backend nodes. |
| number_of_data_files | long | Number of data files. |
| number_of_rounds | long | Number of rounds. |
| number_of_top_queries | long | Number of top queries. |
| number_of_tries | long | Number of tries. |
| object_id | long | Object identifier. |
| observation_end_time | datetime | Observation end time timestamp. |
| observation_metric | string | Observation metric. |
| observation_start_time | datetime | Observation start time timestamp. |
| observed_parallelism | long | Observed parallelism. |
| occurrences | string | Occurrences. |
| offer_categories | string | Offer categories. |
| oldEmailContent | string | Old Email Content. |
| old_failover_state | string | State value for old failover. |
| old_file_service_properties | string | Old file service properties. |
| old_primary_key_hash | string | Old primary key hash. |
| old_scheduler_pattern | string | Old scheduler pattern. |
| old_secondary_key_hash | string | Old secondary key hash. |
| old_server_name | string | Old server name. |
| old_server_resource_group | string | Old server resource group. |
| old_server_subscription_id | string | Old server subscription identifier. |
| old_state | string | State value for old. |
| old_tr_cms_state | string | State value for old tr cms. |
| old_value | string | Old value. |
| one_off_start_time | string | One off start time timestamp. |
| only_update_boot_page | bool | Boolean flag indicating whether only update boot page. |
| open_mode | string | Open mode. |
| operation | string | Operation. |
| operationId | string | Operation Id. |
| operation_category | string | Operation category. |
| operation_count | long | Number of operation. |
| operation_id | string | Operation identifier for the workflow. |
| operation_name | string | Operation name. |
| operation_owner_alias | string | Operation owner alias. |
| operation_parameters | string | Operation parameters. |
| operation_result | string | Operation result. |
| operation_stack | string | Operation stack. |
| operation_status | string | Status value for operation. |
| operation_sub_type | string | Type classification for operation sub. |
| operation_type | string | Type classification for operation. |
| option | string | Option. |
| option_value | string | Option value. |
| ordinal | long | Ordinal. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| original_request_id | string | Original request identifier. |
| original_storage_account_type | string | Type classification for original storage account. |
| outbound_rule_fqdn | string | Outbound rule fqdn. |
| overbookingRatioPercentage | long | Overbooking Ratio Percentage. |
| override_value | string | Override value. |
| overwrite | bool | Boolean flag indicating whether overwrite. |
| owner | string | Owner. |
| ownerLoginNameLength | long | Owner Login Name Length. |
| ownerSid | string | Owner Sid. |
| package | string | Package. |
| pageServerFileSizeInGB | long | Page Server File Size In GB. |
| pair_cluster_address | string | Pair cluster address. |
| parameterization_type | string | Type classification for parameterization. |
| parameters | string | Parameters. |
| parentLogicalServerName | string | Parent Logical Server Name. |
| parse_type | string | Type classification for parse. |
| partition_id | string | Partition identifier. |
| partner_cluster_zone | string | Partner cluster zone. |
| partner_configuration | string | Partner configuration. |
| partner_database_id | string | Partner database identifier. |
| partner_database_name | string | Partner database name. |
| partner_elastic_server_cluster_address | string | Partner elastic server cluster address. |
| partner_elastic_server_id | string | Partner elastic server identifier. |
| partner_elastic_server_name | string | Partner elastic server name. |
| partner_elastic_server_resource_group | string | Partner elastic server resource group. |
| partner_logical_database_name | string | Partner logical database name. |
| partner_logical_server_name | string | Partner logical server name. |
| partner_region | string | Partner region. |
| partner_replica_id | string | Partner replica identifier. |
| partner_replication_endpoint | string | Partner replication endpoint. |
| partner_replication_mode | string | Partner replication mode. |
| partner_replication_role | string | Partner replication role. |
| partner_role | string | Partner role. |
| partner_server | string | Partner server. |
| partner_server_name | string | Partner server name. |
| pause_or_resume | string | Pause or resume. |
| peer_activity_id | string | Peer activity identifier. |
| peer_activity_seq | long | Peer activity seq. |
| peer_address | string | Peer address. |
| peer_port | long | Peer port. |
| per_database_auto_pause_delay | long | Per database auto pause delay. |
| percent_complete | float | Percent complete. |
| percentage_cap | long | Percentage cap. |
| perform_post_health | string | Perform post health. |
| perform_pre_health | string | Perform pre health. |
| permissions | string | Permissions. |
| physical_database_id | string | Physical database identifier. |
| physical_database_name | string | Physical database name. |
| physical_databse_id | string | Physical databse identifier. |
| pinFlagValue | bool | Boolean flag indicating whether pin Flag Value. |
| placement_affinity_tag | string | Placement affinity tag. |
| placement_base_weight | long | Placement base weight. |
| placement_constraints | string | Placement constraints. |
| placement_feature_capacity_tag | string | Placement feature capacity tag. |
| placement_feature_deprioritized_hardware | string | Placement feature deprioritized hardware. |
| placement_feature_hardware | string | Placement feature hardware. |
| placement_feature_name | string | Placement feature name. |
| placement_feature_tr_affinity_tag | string | Placement feature tr affinity tag. |
| placement_feature_tr_name | string | Placement feature tr name. |
| placement_feature_tr_preference_tag | string | Placement feature tr preference tag. |
| placement_feature_xml | string | Placement feature xml. |
| placement_icm_number | long | Placement icm number. |
| placement_id | string | Placement identifier. |
| placement_preference_tag | string | Placement preference tag. |
| placement_preference_tag_isolation_flag | string | Placement preference tag isolation flag. |
| placement_reason | string | Placement reason. |
| placement_reason_tag | string | Placement reason tag. |
| placement_user_name | string | Placement user name. |
| placement_weight | string | Placement weight. |
| placement_xml_bucket | string | Placement xml bucket. |
| plan_id | long | Plan identifier. |
| point_in_time | string | Point in time timestamp. |
| point_in_time_service_level_objective_name | string | Point in time service level objective name. |
| policies | string | Policies. |
| policy | string | Policy. |
| policy_based_external_authorization | string | Policy based external authorization. |
| port | long | Port. |
| post_exec_classifier_ms | long | Post exec classifier ms in milliseconds. |
| pre_deployment_schema_version | long | Pre deployment schema version. |
| pre_provisioning_engine_id | string | Pre provisioning engine identifier. |
| preprovisioned_properties | string | Preprovisioned properties. |
| preprovisioned_properties_id | string | Preprovisioned properties identifier. |
| present_cmw_pattern | string | Present cmw pattern. |
| prevent_data_exfiltration | bool | Boolean flag indicating whether prevent data exfiltration. |
| previous_state | string | State value for previous. |
| primary_availability_group_name | string | Primary availability group name. |
| primary_certificate_name | string | Primary certificate name. |
| primary_certificate_thumbprint | string | Primary certificate thumbprint. |
| primary_compute_bsn_progress | long | Primary compute bsn progress. |
| primary_compute_eol_lsn_hex | string | Primary compute eol lsn hex. |
| principal_type | string | Type classification for principal. |
| priority | string | Priority. |
| priority_vector | string | Priority vector. |
| private_cluster_capacity_management_id | string | Private cluster capacity management identifier. |
| private_cluster_id | string | Private cluster identifier. |
| private_cluster_request_id | string | Private cluster request identifier. |
| private_cluster_subnet_resource_path | string | Private cluster subnet resource path. |
| private_cluster_subscription_affinity_tag | string | Private cluster subscription affinity tag. |
| private_cluster_subscription_tag | string | Private cluster subscription tag. |
| private_endpoint_resource_group_name | string | Private endpoint resource group name. |
| private_endpoint_subscription_id | string | Private endpoint subscription identifier. |
| private_ip_address | string | Private ip address. |
| private_resource_id | string | Private resource identifier. |
| private_vnet_id | string | Private vnet identifier. |
| process_id | long | Process identifier. |
| process_name | string | Process name. |
| product | string | Product. |
| product_family | string | Product family. |
| progress_message_scrubbed | string | Progress message scrubbed. |
| property_name | string | Property name. |
| property_path | string | Property path. |
| property_value | string | Property value. |
| propogate_subscription_properties | string | Propogate subscription properties. |
| protector_type | string | Type classification for protector. |
| provider_type | string | Type classification for provider. |
| provisioning_weight | real | Provisioning weight. |
| proxy_override | string | Proxy override. |
| public_data_endpoint_enabled | bool | Boolean flag indicating whether public data endpoint enabled. |
| public_interface_enabled | bool | Boolean flag indicating whether public interface enabled. |
| public_ip | bool | Boolean flag indicating whether public ip. |
| public_service_level_objective_id | string | Public service level objective identifier. |
| public_service_level_objective_name | string | Public service level objective name. |
| purpose | string | Purpose. |
| quantity | long | Quantity. |
| query_capture_mode | string | Query capture mode. |
| query_id | long | Query identifier. |
| query_name | string | Query name. |
| query_parameters | string | Query parameters. |
| query_plan_hash | string | Query plan hash. |
| query_text | string | Query text. |
| query_text_format | string | Query text format. |
| queue_id | string | Queue identifier. |
| queue_type | long | Type classification for queue. |
| quota_id | string | Quota identifier. |
| quota_value_mb | string | Quota value mb. |
| rank | string | Rank. |
| read_only_endpoint_failover_policy | string | Read only endpoint failover policy. |
| read_scale_units | long | Read scale units. |
| reason | string | Reason. |
| recommended_action | string | Recommended action. |
| recommended_action_name | string | Recommended action name. |
| recommended_action_state | string | State value for recommended action. |
| recommended_elastic_pool_name | string | Recommended elastic pool name. |
| recommended_index_name | string | Recommended index name. |
| recover_request_progress | string | Recover request progress. |
| recovery_action | string | Recovery action. |
| recurringScansInfo | string | Recurring Scans Info. |
| refresh_action_name | string | Refresh action name. |
| region | string | Region. |
| regional_audience_count | long | Number of regional audience. |
| regional_experience_count | long | Number of regional experience. |
| regional_policy_count | long | Number of regional policy. |
| regional_traits | string | Regional traits. |
| regions_to_add | string | Regions to add. |
| rehydration_type | string | Type classification for rehydration. |
| rejection_counter_value | string | Rejection counter value. |
| rejection_criteria | string | Rejection criteria. |
| rejection_threshold | string | Rejection threshold. |
| remote_request_id | string | Remote request identifier. |
| remote_store_backup_containers | string | Remote store backup containers. |
| remove_when_expired | string | Remove when expired. |
| repair_action | string | Repair action. |
| repair_description | string | Repair description. |
| repair_scope | string | Repair scope. |
| repair_task_executor | string | Repair task executor. |
| repair_task_id | string | Repair task identifier. |
| repair_task_impact_level | string | Repair task impact level. |
| repair_task_start_time | string | Repair task start time timestamp. |
| repair_task_state | string | State value for repair task. |
| repair_task_version | long | Repair task version. |
| repl_master_node_name | string | Repl master node name. |
| replica_build_wait_duration | long | Replica build wait duration. |
| replica_count_threshold | long | Replica count threshold. |
| replica_id | long | Replica identifier. |
| replication_id | string | Replication identifier. |
| replication_mode | string | Replication mode. |
| replication_user_name | string | Replication user name. |
| request_body | string | Request body. |
| request_count | long | Number of request. |
| request_event_type | string | Type classification for request event. |
| request_headers | string | Request headers. |
| request_id | string | Request identifier used to correlate the operation. |
| request_method | string | Request method. |
| request_name | string | Request name. |
| request_rank | long | Request rank. |
| request_type | string | Type classification for request. |
| request_uri | string | Request uri. |
| request_uri_scrubbed | string | Request uri scrubbed. |
| request_url | string | Request url. |
| requested_RCSI | string | Requested RCSI. |
| requested_aad_only_auth | bool | Boolean flag indicating whether requested Azure AD only auth. |
| requested_application_type_version | string | Requested application type version. |
| requested_backup_retention_days | real | Requested backup retention days. |
| requested_cmw_pattern | string | Requested cmw pattern. |
| requested_collation | string | Requested collation. |
| requested_common_alias | string | Requested common alias. |
| requested_database_dtu_max | long | Requested database dtu max. |
| requested_database_dtu_min | long | Requested database dtu min. |
| requested_database_name | string | Requested database name. |
| requested_diff_backup_interval_minutes | string | Requested diff backup interval minutes. |
| requested_edition | string | Requested edition. |
| requested_elastic_pool_dtu | long | Requested elastic pool dtu. |
| requested_elastic_pool_edition | string | Requested elastic pool edition. |
| requested_elastic_pool_name | string | Requested elastic pool name. |
| requested_elastic_pool_storage_in_megabytes | long | Requested elastic pool storage in megabytes. |
| requested_encryption | string | Requested encryption. |
| requested_external_admin_login_sid | string | Requested external admin login sid. |
| requested_external_admin_principal_type | long | Type classification for requested external admin principal. |
| requested_internal_service_level_objective_id | string | Requested internal service level objective identifier. |
| requested_internal_service_level_objective_name | string | Requested internal service level objective name. |
| requested_is_free_database_supported | bool | Boolean flag indicating whether requested free database supported. |
| requested_is_max_size_bytes_updated | bool | Requested is max size size in bytes updated. |
| requested_logical_database_edition | string | Requested logical database edition. |
| requested_logical_database_name | string | Requested logical database name. |
| requested_logical_database_slo | string | Requested logical database slo. |
| requested_logical_database_slo_name | string | Requested logical database slo name. |
| requested_logical_server_name | string | Requested logical server name. |
| requested_maint_config_internal_id | string | Requested maint config internal identifier. |
| requested_maintenance_schedule_id | string | Requested maintenance schedule identifier. |
| requested_max_size_bytes | long | Requested max size size in bytes. |
| requested_public_service_level_objective_id | string | Requested public service level objective identifier. |
| requested_public_service_level_objective_name | string | Requested public service level objective name. |
| requested_resource_pool_name | string | Requested resource pool name. |
| requested_result_set_caching | string | Requested result set caching. |
| requested_retention_days | string | Requested retention days. |
| requested_safety_checks | string | Requested safety checks. |
| requested_server_version | string | Requested server version. |
| requested_service_level_objective_id | string | Requested service level objective identifier. |
| requested_state | string | State value for requested. |
| requested_storage_mb | long | Requested storage mb. |
| requested_subscription_id | string | Requested subscription identifier. |
| requested_target_data_file_storage_hints | string | Requested target data file storage hints. |
| requested_target_log_file_storage_hints | string | Requested target log file storage hints. |
| requested_target_sql_instance_name | string | Requested target SQL instance name. |
| requested_target_storage_account_tag | string | Requested target storage account tag. |
| requested_target_storage_account_type | string | Type classification for requested target storage account. |
| requested_target_tenant_ring_name | string | Requested target tenant ring name. |
| requested_target_worker_service_affinity_tag | string | Requested target worker service affinity tag. |
| requested_tenant_id | string | Requested tenant identifier. |
| requested_tenant_ring_name | string | Requested tenant ring name. |
| requested_update_slo_mode | string | Requested update slo mode. |
| required_storage | long | Required storage. |
| required_update_slo_mode | string | Required update slo mode. |
| reservation_id | string | Reservation identifier. |
| reservation_start_date | string | Reservation start date. |
| reservation_term | string | Reservation term. |
| reservation_type | string | Type classification for reservation. |
| reset | bool | Boolean flag indicating whether reset. |
| resize_event_trigger | bool | Boolean flag indicating whether resize event trigger. |
| resolution_dns_name | string | Resolution dns name. |
| resolution_dns_server | string | Resolution dns server. |
| resolution_result | string | Resolution result. |
| resourceTags | string | Resource Tags. |
| resourceValue | string | Resource Value. |
| resource_group_name | string | Resource group name. |
| resource_id | string | Resource identifier. |
| resource_in_expand | string | Resource in expand. |
| resource_name_arguments | string | Resource name arguments. |
| resource_pool_id | string | Resource pool identifier. |
| resource_pool_name | string | Resource pool name. |
| resource_tags | string | Resource tags. |
| resource_type | string | Type classification for resource. |
| resources_being_moved | string | Resources being moved. |
| response_body | string | Response body. |
| response_body_scrubbed | string | Response body scrubbed. |
| response_code | long | Response code. |
| response_content | string | Response content. |
| response_length | long | Response length. |
| response_status | string | Status value for response. |
| response_status_code | string | Response status code. |
| rest_api_version | string | Rest api version. |
| restore_bsn | long | Restore bsn. |
| restore_id | string | Restore identifier. |
| restore_point_name | string | Restore point name. |
| restore_request_id | string | Restore request identifier. |
| restore_status | string | Status value for restore. |
| restore_type | string | Type classification for restore. |
| restoring_replica_node_name | string | Restoring replica node name. |
| result | bool | Boolean flag indicating whether result. |
| retention_period_in_days | string | Retention period in days. |
| retention_policy_name | string | Retention policy name. |
| retry_count | long | Number of retry. |
| retry_interval_ms | long | Retry interval ms in milliseconds. |
| return_code | string | Return code. |
| rg_isolation_property_name | string | Resource governor isolation property name. |
| rg_isolation_property_value | string | Resource governor isolation property value. |
| ring_buildout_id | string | Ring buildout identifier. |
| ring_deployed_id | string | Ring deployed identifier. |
| ring_name | string | Ring name. |
| ring_placement_affinity_tag | string | Ring placement affinity tag. |
| ring_type | string | Type classification for ring. |
| role | string | Role. |
| role_name | string | Role name. |
| role_type | string | Type classification for role. |
| roles | string | Roles. |
| rollout_key_prefix | string | Rollout key prefix. |
| rollout_type | string | Type classification for rollout. |
| rollover_type | string | Type classification for rollover. |
| routes_diff_applied | string | Routes diff applied. |
| routes_diff_cms | string | Routes diff cms. |
| row_count | long | Number of row. |
| rows_count | long | Number of rows. |
| rule_count | long | Number of rule. |
| rule_level | string | Rule level. |
| rule_list_property_found | bool | Boolean flag indicating whether rule list property found. |
| rule_name | string | Rule name. |
| safety_checks_in_progress | bool | Boolean flag indicating whether safety checks in progress. |
| sampleName | string | Sample Name. |
| scanId | string | Scan Id. |
| scanTriggerType | string | Scan Trigger Type. |
| scenario_class_name | string | Scenario class name. |
| scenario_name | string | Scenario name. |
| scenario_parameters | string | Scenario parameters. |
| scenario_status | string | Status value for scenario. |
| schedule_name | string | Schedule name. |
| schedule_sync_interval | long | Schedule sync interval. |
| scheduled_days | string | Scheduled days. |
| scheduled_time_for_remove | datetime | Scheduled time for remove. |
| scheduler_pattern | string | Scheduler pattern. |
| scheduler_type | string | Type classification for scheduler. |
| schemaName | string | Schema Name. |
| schema_deployment_id | string | Schema deployment identifier. |
| schema_name | string | Schema name. |
| schema_version | long | Schema version. |
| scope_name | string | Scope name. |
| secondary_availability_group_name | string | Secondary availability group name. |
| secondary_certificate_name | string | Secondary certificate name. |
| secondary_certificate_thumbprint | string | Secondary certificate thumbprint. |
| secondary_default_value | long | Secondary default value. |
| secondary_service_masterkey_thumbprint | string | Secondary service masterkey thumbprint. |
| secret_create_time | string | Secret create time timestamp. |
| secret_expiration_time | string | Secret expiration time timestamp. |
| secret_type | string | Type classification for secret. |
| security_rules_diff_applied | string | Security rules diff applied. |
| security_rules_diff_cms | string | Security rules diff cms. |
| selected_invalid_container | bool | Boolean flag indicating whether selected invalid container. |
| sellableRatioPercentage | long | Sellable Ratio Percentage. |
| serverType | string | Server Type. |
| server_backup_retention_days | long | Server backup retention days. |
| server_configuration_option_name | string | Server configuration option name. |
| server_configuration_option_value | string | Server configuration option value. |
| server_create_mode | string | Server create mode. |
| server_dns_alias_name | string | Server dns alias name. |
| server_dtu_limit | long | Server dtu limit. |
| server_edition | string | Server edition. |
| server_enable_storage_auto_grow | bool | Boolean flag indicating whether server enable storage auto grow. |
| server_encryption_key_name | string | Server encryption key name. |
| server_features | string | Server features. |
| server_geo_redundant_backup | bool | Boolean flag indicating whether server geo redundant backup. |
| server_name | string | Managed Instance server name. |
| server_quota | string | Server quota. |
| server_role | string | Server role. |
| server_security_credentials | string | Server security credentials. |
| server_state | string | State value for server. |
| server_storage_auto_grow | bool | Boolean flag indicating whether server storage auto grow. |
| server_storage_mb | long | Server storage mb. |
| server_transaction_id | string | Server transaction identifier. |
| server_type | string | Type classification for server. |
| server_usage | long | Server usage. |
| server_version | string | Server version. |
| serviceLevelObjective | string | Service Level Objective. |
| service_account_name | string | Service account name. |
| service_endpoint_policy_id | string | Service endpoint policy identifier. |
| service_endpoint_policy_management_id | string | Service endpoint policy management identifier. |
| service_instance_name | string | Service instance name. |
| service_level_objective | string | Service level objective. |
| service_level_objective_id | string | Service level objective identifier. |
| service_level_objective_name | string | Service level objective name. |
| service_masterkey_thumbprint | string | Service masterkey thumbprint. |
| service_name | string | Service name. |
| service_type | string | Type classification for service. |
| service_type_name | string | Service type name. |
| servicemanifest_name | string | Servicemanifest name. |
| sessionName | string | Session Name. |
| session_guid | string | Session guid. |
| session_id | long | Session identifier. |
| session_recover_ms | long | Session recover ms in milliseconds. |
| session_recovery_format_length | long | Session recovery format length. |
| session_recovery_is_enabled | bool | Boolean flag indicating whether session recovery enabled. |
| session_recovery_is_recovered | bool | Boolean flag indicating whether session recovery recovered. |
| setting_name | string | Setting name. |
| setting_type | string | Type classification for setting. |
| setting_value | string | Setting value. |
| setting_value_resource_name | string | Setting value resource name. |
| settings | string | Settings. |
| should_send_notification | bool | Boolean flag indicating whether should send notification. |
| show_full_list | bool | Boolean flag indicating whether show full list. |
| silent | bool | Boolean flag indicating whether silent. |
| size_based_cleanup_mode | string | Size based cleanup mode. |
| size_in_mb | long | Size in mb. |
| skipValidation | bool | Boolean flag indicating whether skip Validation. |
| skip_business_hours_check | string | Skip business hours check. |
| skip_consistency_check | bool | Boolean flag indicating whether skip consistency check. |
| skip_effective_placement_feature_check | string | Skip effective placement feature check. |
| skip_init_sync | bool | Boolean flag indicating whether skip init sync. |
| skip_instances_check | bool | Boolean flag indicating whether skip instances check. |
| skip_reason | string | Skip reason. |
| skip_verification | bool | Boolean flag indicating whether skip verification. |
| sku | string | Sku. |
| slo_backend | string | Slo backend. |
| slo_dqp | string | Slo dqp. |
| slo_frontend | string | Slo frontend. |
| snapshot_set_id | long | Snapshot set identifier. |
| snapshot_storage_size_mb | long | Snapshot storage size mb. |
| sni_server_name | string | Sni server name. |
| sourceServerName | string | Source Server Name. |
| source_blob_offset | string | Source blob offset. |
| source_blob_uri | string | Source blob uri. |
| source_catalog_database_id | string | Source catalog database identifier. |
| source_cluster_address | string | Source cluster address. |
| source_cluster_name | string | Source cluster name. |
| source_container_uri | string | Source container uri. |
| source_database_dropped_time | string | Source database dropped time timestamp. |
| source_database_id | string | Source database identifier. |
| source_database_name | string | Source database name. |
| source_elastic_server_cluster_address | string | Source elastic server cluster address. |
| source_elastic_server_id | string | Source elastic server identifier. |
| source_elastic_server_name | string | Source elastic server name. |
| source_elastic_server_resource_group | string | Source elastic server resource group. |
| source_endpoint | string | Source endpoint. |
| source_file_path | string | Source file path. |
| source_id | string | Source identifier. |
| source_logical_database_id | string | Source logical database identifier. |
| source_logical_server_id | string | Source logical server identifier. |
| source_logical_server_name | string | Source logical server name. |
| source_managed_database_dropped_time | string | Source managed database dropped time timestamp. |
| source_managed_server_dropped_time | string | Source managed server dropped time timestamp. |
| source_operation_id | string | Source operation identifier. |
| source_physical_database_id | string | Source physical database identifier. |
| source_reservation_id | string | Source reservation identifier. |
| source_resource_group | string | Source resource group. |
| source_resource_group_name | string | Source resource group name. |
| source_server_id | string | Source server identifier. |
| source_server_name | string | Source server name. |
| source_service_level_objective | string | Source service level objective. |
| source_service_level_objective_name | string | Source service level objective name. |
| source_sql_instance_name | string | Source SQL instance name. |
| source_storage_account_mame | string | Source storage account mame. |
| source_storage_container_mame | string | Source storage container mame. |
| source_storage_subscription_id | string | Source storage subscription identifier. |
| source_subscription_id | string | Source subscription identifier. |
| source_time_utc | datetime | Source time utc. |
| source_vnet_name | string | Source vnet name. |
| space_quota | long | Space quota. |
| spid | long | Spid. |
| spinnaker_db_quota | long | Spinnaker database quota. |
| spinnaker_db_usage | long | Spinnaker database usage. |
| sqlDatabaseId | string | SQL Database Id. |
| sqlInstanceName | string | SQL Instance Name. |
| sqlInstance_name | string | SQL Instance name. |
| sql_client_dns_caching_status | long | Status value for SQL client dns caching. |
| sql_command_timeout_sec | long | SQL command timeout sec. |
| sql_error_code | long | SQL error code. |
| sql_error_state | long | State value for SQL error. |
| sql_instance | string | SQL instance. |
| sql_instance_affinity_tag | string | SQL instance affinity tag. |
| sql_instance_id | string | SQL instance identifier. |
| sql_instance_name | string | SQL instance name. |
| sql_instance_refresh_secrets_batch_name | string | SQL instance refresh secrets batch name. |
| sql_server_database_id | string | SQL server database identifier. |
| sql_server_licence | string | SQL server licence. |
| ssl_cipher | string | Ssl cipher. |
| ssl_enqueue_time_ms | long | Ssl enqueue time ms in milliseconds. |
| ssl_hash | string | Ssl hash. |
| ssl_protocol | string | Ssl protocol. |
| ssl_read_time_ms | long | Ssl read time ms in milliseconds. |
| ssl_secure_call_time_ms | long | Ssl secure call time ms in milliseconds. |
| ssl_time_ms | long | Ssl time ms in milliseconds. |
| ssl_write_time_ms | long | Ssl write time ms in milliseconds. |
| sspi_enqueue_time_ms | long | Sspi enqueue time ms in milliseconds. |
| sspi_read_time_ms | long | Sspi read time ms in milliseconds. |
| sspi_secure_call_time_ms | long | Sspi secure call time ms in milliseconds. |
| sspi_time_ms | long | Sspi time ms in milliseconds. |
| sspi_write_time_ms | long | Sspi write time ms in milliseconds. |
| stack_trace | string | Stack trace. |
| stale_query_threshold_days | long | Stale query threshold days. |
| standby_mode | bool | Boolean flag indicating whether standby mode. |
| startDnsName | string | Start Dns Name. |
| startResourceRecordId | string | Start Resource Record Id. |
| start_ip_address | string | Start ip address. |
| start_time | string | Start timestamp. |
| state | string | Current lifecycle or health state. |
| state_desc | string | State desc. |
| state_machine_type | string | Type classification for state machine. |
| status | long | Current status reported by the component. |
| status_code | string | Status code. |
| step_name | string | Step name. |
| storageType | string | Storage Type. |
| storage_account_dnsname | string | Storage account dnsname. |
| storage_account_empty | bool | Boolean flag indicating whether storage account empty. |
| storage_account_kind | string | Storage account kind. |
| storage_account_name | string | Storage account name. |
| storage_account_purpose | string | Storage account purpose. |
| storage_account_resource_group | string | Storage account resource group. |
| storage_account_subscription_id | string | Storage account subscription identifier. |
| storage_account_type | string | Type classification for storage account. |
| storage_container_count | long | Number of storage container. |
| storage_container_metadata_source | string | Storage container metadata source. |
| storage_container_name | string | Storage container name. |
| storage_container_quota_mb | long | Storage container quota mb. |
| storage_container_uri | string | Storage container uri. |
| storage_iops | long | Storage IOPS. |
| storage_key_type | string | Type classification for storage key. |
| storage_mb | long | Storage mb. |
| storage_resource_group | string | Storage resource group. |
| storage_resource_type | string | Type classification for storage resource. |
| storage_size_in_gb | long | Storage size in gb. |
| storage_subscription_id | string | Storage subscription identifier. |
| storage_target_path | string | Storage target path. |
| storage_target_type | string | Type classification for storage target. |
| storage_throughput_mbps | long | Storage throughput mbps. |
| sub_region | string | Sub region. |
| subject_name | string | Subject name. |
| submit_resource_hydration | bool | Boolean flag indicating whether submit resource hydration. |
| subnet_id | string | Subnet identifier. |
| subnet_ip_range | string | Subnet ip range. |
| subnet_name | string | Subnet name. |
| subnet_resource_id | string | Subnet resource identifier. |
| subnet_type | long | Type classification for subnet. |
| subscription_created | string | Subscription created. |
| subscription_creation_date | string | Subscription creation date. |
| subscription_purpose | string | Subscription purpose. |
| subscription_usage | string | Subscription usage. |
| substring_length | long | Substring length. |
| substring_start | long | Substring start. |
| success | bool | Boolean flag indicating whether success. |
| successfull_operations_count | long | Number of successfull operations. |
| supported_server_version | string | Supported server version. |
| synapse_artifact_service_object_version | string | Synapse artifact service object version. |
| synapse_artifact_service_objectid | string | Synapse artifact service objectid. |
| synapse_artifact_service_pending_object_version | string | Synapse artifact service pending object version. |
| syncAgentName | string | Sync Agent Name. |
| syncGroupMode | long | Sync Group Mode. |
| syncGroupName | string | Sync Group Name. |
| sync_agent_id | string | Sync agent identifier. |
| sync_agent_name | string | Sync agent name. |
| sync_application_name | string | Sync application name. |
| sync_db | string | Sync database. |
| sync_direction | string | Sync direction. |
| sync_group_id | string | Sync group identifier. |
| sync_group_name | string | Sync group name. |
| sync_interval_sec | long | Sync interval sec. |
| sync_member_azure_database_resource_id | string | Sync member azure database resource identifier. |
| sync_member_id | string | Sync member identifier. |
| sync_member_name | string | Sync member name. |
| sync_member_resource_id | string | Sync member resource identifier. |
| sync_server | string | Sync server. |
| syncdb_logical_database_name | string | Syncdb logical database name. |
| syncdb_logical_server_name | string | Syncdb logical server name. |
| syncdb_resource_group | string | Syncdb resource group. |
| syncdb_subscription_id | string | Syncdb subscription identifier. |
| system_cpu_time_milliseconds | real | System CPU time in milliseconds. |
| system_metadata_arguments | string | System metadata arguments. |
| tableName | string | Table Name. |
| table_name | string | Table name. |
| target | string | Target. |
| targetServerName | string | Target Server Name. |
| target_blob_offset | string | Target blob offset. |
| target_blob_tier | string | Target blob tier. |
| target_blob_uri | string | Target blob uri. |
| target_catalog_database_id | string | Target catalog database identifier. |
| target_cluster_zone | string | Target cluster zone. |
| target_collation | string | Target collation. |
| target_container_uri | string | Target container uri. |
| target_database_name | string | Target database name. |
| target_db_file_path | string | Target database file path. |
| target_db_name | string | Target database name. |
| target_db_node_count | long | Number of target database node. |
| target_edition | string | Target edition. |
| target_failover_state | string | State value for target failover. |
| target_file_name | string | Target file name. |
| target_file_path | string | Target file path. |
| target_gateway_slice_id | string | Target gateway slice identifier. |
| target_hardware_family | string | Target hardware family. |
| target_host_name | string | Target host name. |
| target_is_mi_link_disaster_recovery_only | string | Target is MI link disaster recovery only. |
| target_logical_database_id | string | Target logical database identifier. |
| target_logical_database_name | string | Target logical database name. |
| target_logical_server_name | string | Target logical server name. |
| target_managed_server_name | string | Target managed server name. |
| target_node_name | string | Target node name. |
| target_physical_database_id | string | Target physical database identifier. |
| target_port | long | Target port. |
| target_public_ip | bool | Boolean flag indicating whether target public ip. |
| target_replica_count | long | Number of target replica. |
| target_replica_set_size | long | Target replica set size. |
| target_reservation_id_one | string | Target reservation id one. |
| target_reservation_id_two | string | Target reservation id two. |
| target_reservation_quantity_one | long | Target reservation quantity one. |
| target_reservation_quantity_two | long | Target reservation quantity two. |
| target_resource_group | string | Target resource group. |
| target_resource_group_name | string | Target resource group name. |
| target_schema_version | long | Target schema version. |
| target_server_name | string | Target server name. |
| target_server_version | string | Target server version. |
| target_service_instance_name | string | Target service instance name. |
| target_service_level_objective | string | Target service level objective. |
| target_service_level_objective_name | string | Target service level objective name. |
| target_size | long | Target size. |
| target_slo | string | Target slo. |
| target_sql_instance_name | string | Target SQL instance name. |
| target_sql_server_licence | string | Target SQL server licence. |
| target_storage_account_name | string | Target storage account name. |
| target_storage_container_name | string | Target storage container name. |
| target_storage_iops | long | Target storage IOPS. |
| target_storage_size_in_gb | long | Target storage size in gb. |
| target_storage_subscription_id | string | Target storage subscription identifier. |
| target_storage_throughput_mbps | long | Target storage throughput mbps. |
| target_storage_type | string | Type classification for target storage. |
| target_subnet_id | string | Target subnet identifier. |
| target_subscription_id | string | Target subscription identifier. |
| target_tenant_ring_name | string | Target tenant ring name. |
| target_tier | string | Target tier. |
| target_total_memory_mb | long | Target total memory mb. |
| target_uri | string | Target uri. |
| target_vcore_count | long | Number of target vCore. |
| target_version | long | Target version. |
| target_vm_sizes | string | Target vm sizes. |
| target_vnet_name | string | Target vnet name. |
| target_workspaces_count | long | Number of target workspaces. |
| task_count | long | Number of task. |
| task_executor_filter | string | Task executor filter. |
| task_id_filter | string | Task id filter. |
| task_state_filter | string | Task state filter. |
| tds_version | long | Tds version. |
| tenantId | string | Tenant Id. |
| tenant_id | string | Tenant identifier. |
| tenant_ring_dns_name | string | Tenant ring dns name. |
| tenant_ring_maintenance_schedule_id | string | Tenant ring maintenance schedule identifier. |
| tenant_ring_name | string | Tenant ring name. |
| tenant_ring_selection_phase | string | Tenant ring selection phase. |
| term | string | Term. |
| test_hook_for_cross_cluster_copy | string | Test hook for cross cluster copy. |
| throttling_threshold | long | Throttling threshold. |
| thumbprint | string | Thumbprint. |
| thumbprints | string | Thumbprints. |
| time_grain | string | Time grain. |
| time_of_upgrade | string | Time of upgrade. |
| time_to_live | string | Time to live. |
| time_to_live_seconds | real | Time to live seconds. |
| timeout_in_seconds | long | Timeout in seconds. |
| timezoneId | string | Timezone Id. |
| timezone_id | string | Timezone identifier. |
| total_blobs | long | Total blobs. |
| total_bytes | long | Total size in bytes. |
| total_capacity | long | Total capacity. |
| total_memory_mb | long | Total memory mb. |
| total_time_ms | long | Total time ms. |
| tr_count | long | Number of tr. |
| traceFlags | string | Trace Flags. |
| trace_event_type | long | Type classification for trace event. |
| traffic_manager_name | string | Traffic manager name. |
| traffic_manager_subscription_id | string | Traffic manager subscription identifier. |
| transaction_id | string | Transaction identifier. |
| transaction_name | string | Transaction name. |
| transfer_rate_mb_sec | long | Transfer rate mb sec. |
| transparent_database_encryption | string | Transparent database encryption. |
| transport_id | string | Transport identifier. |
| truncate_option | string | Truncate option. |
| ttl | long | Ttl. |
| type | string | Type. |
| unsuccessfull_operations_count | long | Number of unsuccessfull operations. |
| update_slo_mode | string | Update slo mode. |
| update_time | string | Update time timestamp. |
| upgrade_domain_timeout | string | Upgrade domain timeout. |
| upgrade_mode | string | Upgrade mode. |
| upgrade_order | string | Upgrade order. |
| upgrade_replica_set_check_timeout | string | Upgrade replica set check timeout. |
| upgrade_timeout | string | Upgrade timeout. |
| upsert_managed_server_request_id | string | Upsert managed server request identifier. |
| uri | string | Uri. |
| use_db_database_firewall_rules_time_ms | long | Use database database firewall rules time ms in milliseconds. |
| use_latest_app_version | bool | Boolean flag indicating whether use latest app version. |
| use_private_link_connection | bool | Boolean flag indicating whether use private link connection. |
| used_login_thread_pool | bool | Boolean flag indicating whether used login thread pool. |
| user | string | User. |
| user_agent | string | User agent. |
| user_cpu_time_milliseconds | real | User CPU time in milliseconds. |
| username | string | Username. |
| utility_database_partition_number | long | Utility database partition number. |
| utility_database_type_name | string | Utility database type name. |
| v2EmailContent | string | V2 Email Content. |
| v_cores | string | V cores. |
| validate_only | bool | Boolean flag indicating whether validate only. |
| value | string | Value. |
| values | string | Values. |
| vault_container_name | string | Vault container name. |
| vault_name | string | Vault name. |
| vault_protected_item_name | string | Vault protected item name. |
| vault_recovery_point_id | string | Vault recovery point identifier. |
| vault_resource_group_name | string | Vault resource group name. |
| vault_subscription_id | string | Vault subscription identifier. |
| vault_tenant_id | string | Vault tenant identifier. |
| vcore_count | long | Number of vCore. |
| vcore_quota | string | VCore quota. |
| vcores | real | Vcores. |
| vdw_frontend_name | string | Vdw frontend name. |
| vdw_pool_id | string | Vdw pool identifier. |
| vdw_pool_ids | string | Vdw pool ids. |
| vdw_pool_name | string | Vdw pool name. |
| verb | string | Verb. |
| version | string | Version. |
| virtual_cluster_name | string | Virtual cluster name. |
| vldb_elastic_pool_id | string | Vldb elastic pool identifier. |
| vldb_elastic_pool_name | string | Vldb elastic pool name. |
| vlf_size_in_mb | long | Vlf size in mb. |
| vm_max_supported_storage | long | Vm max supported storage. |
| vm_size | string | Vm size. |
| vmss_name | string | Vmss name. |
| vnet_dest_peer_address | string | Vnet dest peer address. |
| vnet_gre_key | long | Vnet gre key. |
| vnet_guid | string | Vnet guid. |
| vnet_ip_range | string | Vnet ip range. |
| vnet_link_identifier | long | Vnet link identifier. |
| vnet_name | string | Vnet name. |
| vnet_peer_address | string | Vnet peer address. |
| vnet_region_id | long | Vnet region identifier. |
| vnet_resource_id | string | Vnet resource identifier. |
| vnet_subnet_id | long | Vnet subnet identifier. |
| wait_for_start_copy | bool | Boolean flag indicating whether wait for start copy. |
| weight | string | Weight. |
| window_duration | string | Window duration. |
| winfab_property_name | string | Winfab property name. |
| work_item_id | string | Work item identifier. |
| workflow_category | string | Workflow category. |
| workflow_operation_name | string | Workflow operation name. |
| workflow_uri | string | Workflow uri. |
| workspace_id | string | Workspace identifier. |
| workspace_name | string | Workspace name. |
| xlog_storage_size_mb | long | Xlog storage size mb. |
| xms_client_app_type | string | Type classification for xms client app. |
| xodbc_authentication_time_ms | long | Xodbc authentication time ms in milliseconds. |
| xodbc_authentication_type | int | Type classification for xodbc authentication. |
| xtp_enabled | string | In-Memory OLTP enabled. |
| zone | string | Zone. |
| zoneName | string | Zone Name. |
| zone_resilience_mismatch | bool | Boolean flag indicating whether zone resilience mismatch. |
| zone_resilient | bool | Boolean flag indicating whether zone resilient. |

## MonManagementExceptions — Management Exceptions

**Purpose**: Management Exceptions. Used to investigate platform automation, deployment, cluster configuration, and provisioning workflows. Referenced in MI template areas: backup-restore.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| event | string | Event name emitted by the component. |
| exception_type | string | Type classification for exception. |
| level | string | Level. |
| message | string | Human-readable message text. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| process_id | long | Process identifier. |
| request_id | string | Request identifier used to correlate the operation. |
| sessionName | string | Session Name. |
| stack_trace | string | Stack trace. |

## MonManagementOperations — Management Operations

**Purpose**: Management Operations. Used to investigate platform automation, deployment, cluster configuration, and provisioning workflows. Referenced in MI template areas: availability, backup-restore, networking, performance. Often used during backup or restore investigations.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| active_state_machines | string | Active state machines. |
| assigned_update_slo_mode | string | Assigned update slo mode. |
| automated_cluster_id | string | Automated cluster identifier. |
| buildout_cluster_configuration | string | Buildout cluster configuration. |
| byok_enabled | bool | Boolean flag indicating whether byok enabled. |
| cab_id | long | Cab identifier. |
| client_address | string | Client address. |
| cluster_address | string | Cluster address. |
| cluster_validation_id | string | Cluster validation identifier. |
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| configurations | string | Configurations. |
| conflict_logging_retention_in_days | long | Conflict logging retention in days. |
| conflict_resolution_policy | string | Conflict resolution policy. |
| create_mode | string | Create mode. |
| current_db_node_count | long | Number of current database node. |
| current_server_version | string | Current server version. |
| data_exfiltration_settings | string | Data exfiltration settings. |
| database_charset | string | Database charset. |
| database_collation | string | Database collation. |
| database_create_time | string | Database create time timestamp. |
| database_name | string | Database name. |
| desired_update_slo_mode | string | Desired update slo mode. |
| dns_zone | string | Dns zone. |
| dss_error_message | string | Dss error message. |
| dtu | long | Dtu. |
| edition | string | Edition. |
| elapsed_time | string | Elapsed duration for the operation. |
| elapsed_time_milliseconds | real | Elapsed duration in milliseconds. |
| elastic_pool_id | string | Elastic pool identifier. |
| elastic_server_id | string | Elastic server identifier. |
| elastic_server_instance_name | string | Elastic server instance name. |
| elastic_server_name | string | Elastic server name. |
| enable_conflict_logging | bool | Boolean flag indicating whether enable conflict logging. |
| enable_infrastructure_encryption | bool | Boolean flag indicating whether enable infrastructure encryption. |
| end_ip_address | string | End ip address. |
| error_classification | string | Error classification. |
| error_code | long | Numeric error code for the failure or event. |
| error_message | string | Error message. |
| error_message_systemmetadata | string | Error message systemmetadata. |
| error_severity | long | Error severity. |
| event | string | Event name emitted by the component. |
| exception_message | string | Exception message. |
| exception_type | string | Type classification for exception. |
| force | bool | Boolean flag indicating whether force. |
| hardware_family | string | Hardware family. |
| identity_principal_id | string | Identity principal identifier. |
| identity_tenant_id | string | Identity tenant identifier. |
| identity_url | string | Identity url. |
| ignoreMissingVnetServiceEndpoint | bool | Boolean flag indicating whether ignore Missing Vnet Service Endpoint. |
| ignore_for_Anomaly | bool | Boolean flag indicating whether ignore for Anomaly. |
| instance_pool_name | string | Instance pool name. |
| is_billable | bool | Boolean flag indicating whether billable. |
| is_replace_action | bool | Boolean flag indicating whether replace action. |
| is_unhandled_fsm_user_exception | bool | Boolean flag indicating whether unhandled fsm user exception. |
| is_user_error | bool | Boolean flag indicating whether user error. |
| job_account_id | string | Job account identifier. |
| job_account_name | string | Job account name. |
| level | string | Level. |
| logical_database_id | string | Logical database identifier. |
| logical_database_name | string | Logical database name. |
| logical_server_id | string | Logical server identifier. |
| logical_server_operation_type | string | Type classification for logical server operation. |
| logical_server_state | string | State value for logical server. |
| managed_server_name | string | Managed server name. |
| management_operation_name | string | Management operation name. |
| member_database_name | string | Member database name. |
| member_database_server_name | string | Member database server name. |
| member_database_type | string | Type classification for member database. |
| message | string | Human-readable message text. |
| message_systemmetadata | string | Message systemmetadata. |
| minimal_tls_version | string | Minimal tls version. |
| operation_category | string | Operation category. |
| operation_owner_alias | string | Operation owner alias. |
| operation_parameters | string | Operation parameters. |
| operation_result | string | Operation result. |
| operation_sub_type | string | Type classification for operation sub. |
| operation_type | string | Type classification for operation. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| partner_elastic_server_cluster_address | string | Partner elastic server cluster address. |
| partner_elastic_server_id | string | Partner elastic server identifier. |
| partner_elastic_server_name | string | Partner elastic server name. |
| partner_elastic_server_resource_group | string | Partner elastic server resource group. |
| prevent_data_exfiltration | bool | Boolean flag indicating whether prevent data exfiltration. |
| previous_state | string | State value for previous. |
| private_resource_id | string | Private resource identifier. |
| process_id | long | Process identifier. |
| product_family | string | Product family. |
| proxy_override | string | Proxy override. |
| public_interface_enabled | bool | Boolean flag indicating whether public interface enabled. |
| queue_id | string | Queue identifier. |
| queue_type | long | Type classification for queue. |
| read_scale_units | long | Read scale units. |
| rejection_counter_value | string | Rejection counter value. |
| rejection_criteria | string | Rejection criteria. |
| rejection_threshold | string | Rejection threshold. |
| request_id | string | Request identifier used to correlate the operation. |
| request_rank | long | Request rank. |
| requested_elastic_pool_storage_in_megabytes | long | Requested elastic pool storage in megabytes. |
| requested_service_level_objective_id | string | Requested service level objective identifier. |
| requested_tenant_ring_name | string | Requested tenant ring name. |
| required_update_slo_mode | string | Required update slo mode. |
| resource_pool_create_time | string | Resource pool create time timestamp. |
| resource_pool_name | string | Resource pool name. |
| resource_tags | string | Resource tags. |
| ring_type | string | Type classification for ring. |
| rule_name | string | Rule name. |
| schedule_sync_interval | long | Schedule sync interval. |
| secret_create_time | string | Secret create time timestamp. |
| secret_expiration_time | string | Secret expiration time timestamp. |
| server_backup_retention_days | long | Server backup retention days. |
| server_dtu_limit | long | Server dtu limit. |
| server_edition | string | Server edition. |
| server_enable_storage_auto_grow | bool | Boolean flag indicating whether server enable storage auto grow. |
| server_geo_redundant_backup | bool | Boolean flag indicating whether server geo redundant backup. |
| server_storage_mb | long | Server storage mb. |
| server_type | string | Type classification for server. |
| server_version | string | Server version. |
| service_level_objective | string | Service level objective. |
| service_level_objective_id | string | Service level objective identifier. |
| service_level_objective_name | string | Service level objective name. |
| sessionName | string | Session Name. |
| skip_init_sync | bool | Boolean flag indicating whether skip init sync. |
| source_elastic_server_cluster_address | string | Source elastic server cluster address. |
| source_elastic_server_id | string | Source elastic server identifier. |
| source_elastic_server_name | string | Source elastic server name. |
| source_elastic_server_resource_group | string | Source elastic server resource group. |
| sql_instance_name | string | SQL instance name. |
| sql_server_database_id | string | SQL server database identifier. |
| sql_server_licence | string | SQL server licence. |
| stack_trace | string | Stack trace. |
| start_ip_address | string | Start ip address. |
| state | string | Current lifecycle or health state. |
| storage_iops | long | Storage IOPS. |
| storage_mb | long | Storage mb. |
| storage_size_in_gb | long | Storage size in gb. |
| storage_throughput_mbps | long | Storage throughput mbps. |
| sub_region | string | Sub region. |
| subnetName | string | Subnet Name. |
| subnet_id | string | Subnet identifier. |
| sync_agent_name | string | Sync agent name. |
| sync_direction | string | Sync direction. |
| sync_group_name | string | Sync group name. |
| sync_member_azure_database_resource_id | string | Sync member azure database resource identifier. |
| sync_member_name | string | Sync member name. |
| sync_member_resource_id | string | Sync member resource identifier. |
| syncdb_logical_database_name | string | Syncdb logical database name. |
| syncdb_logical_server_name | string | Syncdb logical server name. |
| syncdb_resource_group | string | Syncdb resource group. |
| syncdb_subscription_id | string | Syncdb subscription identifier. |
| target_db_node_count | long | Number of target database node. |
| target_server_version | string | Target server version. |
| tenant_id | string | Tenant identifier. |
| tenant_ring_name | string | Tenant ring name. |
| thumbprint | string | Thumbprint. |
| total_memory_mb | long | Total memory mb. |
| transaction_id | string | Transaction identifier. |
| use_private_link_connection | bool | Boolean flag indicating whether use private link connection. |
| vcore_count | long | Number of vCore. |
| version | string | Version. |
| vnetFirewallRules | string | Vnet Firewall Rules. |
| vnetName | string | Vnet Name. |
| vnetProviderName | string | Vnet Provider Name. |
| vnetResourceGroupName | string | Vnet Resource Group Name. |
| vnetSubscriptionId | string | Vnet Subscription Id. |

## MonManagementResourceProvider — Management Resource Provider

**Purpose**: Management Resource Provider. Used to investigate platform automation, deployment, cluster configuration, and provisioning workflows. Referenced in MI template areas: backup-restore, general, networking. Often used during failover or replica troubleshooting. Often used during backup or restore investigations.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| account_owner_puid | string | Account owner puid. |
| action_name | string | Action name. |
| actual_state | string | State value for actual. |
| administrator_name | string | Administrator name. |
| administrator_operation_id | string | Administrator operation identifier. |
| administrator_sid | string | Administrator sid. |
| advisor_auto_execute_value | string | Advisor auto execute value. |
| advisor_name | string | Advisor name. |
| api_consumption_percentage | real | Api consumption pe percentage. |
| api_version | string | Api version. |
| archived_backup_resource_id | string | Archived backup resource identifier. |
| azure_async_operation_header | string | Azure async operation header. |
| azure_vault_id | string | Azure vault identifier. |
| backup_archival_policy | string | Backup archival policy. |
| backup_archival_policy_name | string | Backup archival policy name. |
| backup_archival_vault_name | string | Backup archival vault name. |
| body_size | long | Body size. |
| caller_address | string | Caller address. |
| client_request_id | string | Client request identifier. |
| client_routing_id | string | Client routing identifier. |
| client_session_id | string | Client session identifier. |
| cluster_list | string | Cluster list. |
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| connection_type | string | Type classification for connection. |
| content_length | long | Content length. |
| content_type | string | Type classification for content. |
| controller_name | string | Controller name. |
| correlation_id | string | Correlation identifier used across components. |
| count | long | Number of count. |
| create_mode | string | Create mode. |
| current_active_requests | long | Current active requests. |
| database_operation_id | string | Database operation identifier. |
| dsts_authentication_type | string | Type classification for dsts authentication. |
| dsts_dns_name | string | Dsts dns name. |
| dsts_realm | string | Dsts realm. |
| dwquery_id | string | Dwquery identifier. |
| edition | string | Edition. |
| elapsed_time | string | Elapsed duration for the operation. |
| elapsed_time_milliseconds | real | Elapsed duration in milliseconds. |
| elastic_pool | string | Elastic pool. |
| elastic_pool_name | string | Elastic pool name. |
| end_ip | string | End ip. |
| endpoint_consumption_percentage | real | Endpoint consumption pe percentage. |
| endpoint_name | string | Endpoint name. |
| error_description_code | string | Error description code. |
| event | string | Event name emitted by the component. |
| event_context | string | Event context. |
| exception_http_code | long | Exception http code. |
| exception_message | string | Exception message. |
| exception_type | string | Type classification for exception. |
| extra_parameters | string | Extra parameters. |
| fallback_culture | string | Fallback culture. |
| filter_value | string | Filter value. |
| firewall_rule_name | string | Firewall rule name. |
| friendly_name | string | Friendly name. |
| headers | string | Headers. |
| host_id | string | Host identifier. |
| host_name | string | Host name. |
| http_verb | string | Http verb. |
| id | long | identifier. |
| is_continous | string | Boolean flag indicating whether continous. |
| is_forced_terminate | string | Boolean flag indicating whether forced terminate. |
| is_offline_secondary | string | Boolean flag indicating whether offline secondary. |
| is_trusted_client_cert | string | Boolean flag indicating whether trusted client cert. |
| level | string | Level. |
| location_header | string | Location header. |
| location_name | string | Location name. |
| location_placement_id | string | Location placement identifier. |
| logical_database_name | string | Logical database name. |
| logical_elastic_pool_name | string | Logical elastic pool name. |
| logical_operation_stack | string | Logical operation stack. |
| masked_client_ip_address | string | Masked client ip address. |
| max_size_bytes | long | Max size size in bytes. |
| message | string | Human-readable message text. |
| message_resourcename | string | Message resourcename. |
| method_name | string | Method name. |
| module_name | string | Module name. |
| name | string | Object or resource name. |
| offer_categories | string | Offer categories. |
| offer_category | string | Offer category. |
| operation_name | string | Operation name. |
| operation_stack | string | Operation stack. |
| operation_type | string | Type classification for operation. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| partner_database | string | Partner database. |
| partner_server | string | Partner server. |
| process_id | long | Process identifier. |
| query | string | Query. |
| query_id | long | Query identifier. |
| quota_id | string | Quota identifier. |
| read_scaleout | string | Read scaleout. |
| recommended_elastic_pool_name | string | Recommended elastic pool name. |
| recommended_index_name | string | Recommended index name. |
| request_id | string | Request identifier used to correlate the operation. |
| request_url | string | Request url. |
| requested_culture | string | Requested culture. |
| requested_edition | string | Requested edition. |
| requested_elastic_pool_capacity | string | Requested elastic pool capacity. |
| requested_elastic_pool_dtu_max | string | Requested elastic pool dtu max. |
| requested_elastic_pool_dtu_min | string | Requested elastic pool dtu min. |
| requested_elastic_pool_storage_mb | string | Requested elastic pool storage mb. |
| requested_encryption | string | Requested encryption. |
| requested_logical_database_name | string | Requested logical database name. |
| requested_logical_elastic_pool_name | string | Requested logical elastic pool name. |
| requested_max_size_bytes | string | Requested max size size in bytes. |
| requested_service_objective_id | string | Requested service objective identifier. |
| requested_tier | string | Requested tier. |
| requested_transparent_data_encryption_status | string | Status value for requested transparent data encryption. |
| resource_name | string | Resource name. |
| resource_type | string | Type classification for resource. |
| response_body_size | long | Response body size. |
| response_code | long | Response code. |
| response_content | string | Response content. |
| restore_point_in_time | string | Restore point in time timestamp. |
| schema_name | string | Schema name. |
| server_quota | string | Server quota. |
| server_version | string | Server version. |
| service_dns_name | string | Service dns name. |
| service_name | string | Service name. |
| service_objective_id | string | Service objective identifier. |
| service_tier_advisor_name | string | Service tier advisor name. |
| sessionName | string | Session Name. |
| source_database_deletion_date | string | Source database deletion date. |
| source_database_id | string | Source database identifier. |
| source_database_name | string | Source database name. |
| source_instance_name | string | Source instance name. |
| stack_trace | string | Stack trace. |
| start_ip | string | Start ip. |
| state | string | Current lifecycle or health state. |
| subscription_created | string | Subscription created. |
| subscription_state | string | State value for subscription. |
| susbcription_request_type | string | Type classification for susbcription request. |
| table_name | string | Table name. |
| target_cluster_address | string | Target cluster address. |
| target_database_name | string | Target database name. |
| target_server_name | string | Target server name. |
| target_utc_point_in_time | string | Target utc point in time timestamp. |
| tenantId | string | Tenant Id. |
| tenant_id | string | Tenant identifier. |
| trace_message | string | Trace message. |
| trace_source | string | Trace source. |
| transparent_data_encryption_name | string | Transparent data encryption name. |
| update_or_create | string | Update or create. |
| user_agent | string | User agent. |
| value | string | Value. |
| x_ms_client_app_id | string | X ms client app identifier. |
| zone_redundant | bool | Boolean flag indicating whether zone redundant. |

## MonPrivateClusterCapacityManagement — Private Cluster Capacity Management

**Purpose**: Private Cluster Capacity Management. Used to investigate platform automation, deployment, cluster configuration, and provisioning workflows. Referenced in MI template areas: availability.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| aad_tenant_id | string | Azure AD tenant identifier. |
| architecture_version | string | Architecture version. |
| code_package_version | string | Code package version. |
| concurrency_token | long | Concurrency token. |
| cosmos_db_account_name | string | Cosmos database account name. |
| create_time | datetime | Creation timestamp. |
| current_total_number_of_nodes | long | Current total number of nodes. |
| dns_prefix | string | Dns prefix. |
| dns_servers | string | Dns servers. |
| end_utc_date | datetime | End utc date. |
| fsm_context_instance_name | string | Fsm context instance name. |
| fsm_extension_data | string | Fsm extension data. |
| fsm_instance_id | string | Fsm instance identifier. |
| fsm_timer_event_version | long | Fsm timer event version. |
| fsm_version | long | Fsm version. |
| is_error_state | long | Boolean flag indicating whether error state. |
| is_multi_nic_subnet | long | Boolean flag indicating whether multi nic subnet. |
| is_stable_state | long | Boolean flag indicating whether stable state. |
| is_swift_subnet | long | Boolean flag indicating whether swift subnet. |
| last_exception | string | Last exception. |
| last_state_change_time | datetime | Last state change time timestamp. |
| last_subnet_seps_count | long | Number of last subnet seps. |
| last_subnet_seps_count_time | datetime | Last subnet seps count time timestamp. |
| last_update_time | datetime | Last update time timestamp. |
| migration_state | string | State value for migration. |
| migration_type | string | Type classification for migration. |
| next_successor | long | Next successor. |
| private_cluster_capacity_management_id | string | Private cluster capacity management identifier. |
| request_id | string | Request identifier used to correlate the operation. |
| requested_capacity_counts | string | Requested capacity counts. |
| requested_upgrade_capacity_counts | string | Requested upgrade capacity counts. |
| resource_tags | string | Resource tags. |
| start_utc_date | datetime | Start utc date. |
| state | string | Current lifecycle or health state. |
| subnet_address_range | string | Subnet address range. |
| subnet_name | string | Subnet name. |
| subnet_resource_id | string | Subnet resource identifier. |
| target_number_of_nodes_per_role | string | Target number of nodes per role. |
| virtual_cluster_name | string | Virtual cluster name. |
| vnet_intent_policy | string | Vnet intent policy. |
| vnet_intent_policy_additional_rules | string | Vnet intent policy additional rules. |
| vnet_intent_policy_resource_id | string | Vnet intent policy resource identifier. |
| vnet_resource_guid | string | Vnet resource guid. |
| vnet_resource_id | string | Vnet resource identifier. |
| vnet_resource_id_lock | string | Vnet resource id lock. |

## MonPrivateClusters — Private Clusters

**Purpose**: Private Clusters. Used to investigate platform automation, deployment, cluster configuration, and provisioning workflows. Referenced in MI template areas: availability, general, networking.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| PartitionId | string | Partition Id. |
| aad_tenant_id | string | Azure AD tenant identifier. |
| buffered_capacity_counts | string | Buffered capacity counts. |
| code_package_version | string | Code package version. |
| concurrency_token | long | Concurrency token. |
| create_time | datetime | Creation timestamp. |
| custom_maintenance_window_scheduler_pattern | string | Custom maintenance window scheduler pattern. |
| dns_prefix | string | Dns prefix. |
| eligible_roles_for_cogs_saving | string | Eligible roles for cogs saving. |
| end_utc_date | datetime | End utc date. |
| foreground_drop_completed | long | Foreground drop completed. |
| fsm_context_instance_name | string | Fsm context instance name. |
| fsm_extension_data | string | Fsm extension data. |
| fsm_instance_id | string | Fsm instance identifier. |
| fsm_timer_event_version | long | Fsm timer event version. |
| fsm_version | long | Fsm version. |
| hardware_family | string | Hardware family. |
| infra_subnet_manager_id | string | Infra subnet manager identifier. |
| internal_load_balancer_ip_address | string | Internal load balancer ip address. |
| is_error_state | long | Boolean flag indicating whether error state. |
| is_grip | long | Boolean flag indicating whether grip. |
| is_resizable | long | Boolean flag indicating whether resizable. |
| is_stable_state | long | Boolean flag indicating whether stable state. |
| is_swift | long | Boolean flag indicating whether swift. |
| is_taken_from_preprovisioned_pool | long | Boolean flag indicating whether taken from preprovisioned pool. |
| last_exception | string | Last exception. |
| last_resized | datetime | Last resized. |
| last_state_change_time | datetime | Last state change time timestamp. |
| last_update_time | datetime | Last update time timestamp. |
| maintenance_policy_id | string | Maintenance policy identifier. |
| managed_instance_pool_id | string | Managed instance pool identifier. |
| maximum_number_of_nodes | long | Maximum number of nodes. |
| minimum_number_of_nodes | string | Minimum number of nodes. |
| name | string | Object or resource name. |
| next_successor | long | Next successor. |
| pre_provisioned_properties | string | Pre provisioned properties. |
| private_cluster_id | string | Private cluster identifier. |
| private_cluster_resource_id | string | Private cluster resource identifier. |
| request_id | string | Request identifier used to correlate the operation. |
| retention_period_in_days | long | Retention period in days. |
| ring_buildout_id | string | Ring buildout identifier. |
| scheduled_time_for_remove | datetime | Scheduled time for remove. |
| start_utc_date | datetime | Start utc date. |
| state | string | Current lifecycle or health state. |
| subnet_address_range | string | Subnet address range. |
| subnet_name | string | Subnet name. |
| subnet_resource_id | string | Subnet resource identifier. |
| supports_self_service_maintenance | long | Supports self service maintenance. |
| tenant_ring_name | string | Tenant ring name. |
| vnet_intent_policy | string | Vnet intent policy. |
| vnet_intent_policy_additional_rules | string | Vnet intent policy additional rules. |
| vnet_intent_policy_resource_id | string | Vnet intent policy resource identifier. |
| vnet_resource_guid | string | Vnet resource guid. |
| vnet_resource_id | string | Vnet resource identifier. |

## MonRolloutProgress — Rollout Progress

**Purpose**: Rollout Progress. Used to investigate platform automation, deployment, cluster configuration, and provisioning workflows. Referenced in MI template areas: availability, backup-restore, networking. Often used to correlate SQL behavior with Service Fabric activity.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| BytesTransferred | long | Bytes Transferred. |
| NumberOfFilesFailed | long | Number Of Files Failed. |
| NumberOfFilesSkipped | long | Number Of Files Skipped. |
| NumberOfFilesTransferred | long | Number Of Files Transferred. |
| _nextTimeToDoWorkValueSource | string | Next Time To Do Work Value Source. |
| action | string | Action. |
| actual_block_state | string | State value for actual block. |
| affinity_tag | string | Affinity tag. |
| aggregate_health_state | string | State value for aggregate health. |
| api_request_body | string | Api request body. |
| api_response_body | string | Api response body. |
| app_last_unpin_time | datetime | App last unpin time timestamp. |
| app_unpin_long_enough | bool | Boolean flag indicating whether app unpin long enough. |
| application_build_path | string | Application build path. |
| application_health | string | Application health. |
| application_name | string | Application name. |
| application_type_configuration_phase | string | Application type configuration phase. |
| application_type_name | string | Application type name. |
| application_type_overrides | string | Application type overrides. |
| application_type_version | string | Application type version. |
| apps_allowed_to_upgrade_count | real | Number of apps allowed to upgrade. |
| apps_allowed_to_upgrade_size | real | Apps allowed to upgrade size. |
| apps_post_health_check_count | long | Number of apps post health check. |
| apps_post_health_check_size | long | Apps post health check size. |
| async_action_execution_status | string | Status value for async action execution. |
| async_action_input_type | string | Type classification for async action input. |
| async_action_output_type | string | Type classification for async action output. |
| async_action_type | string | Type classification for async action. |
| attempt | long | Attempt. |
| auto_action_kind | string | Auto action kind. |
| auto_resume | bool | Boolean flag indicating whether auto resume. |
| auto_resume_count | long | Number of auto resume. |
| azure_comms_communication_id | string | Azure comms communication identifier. |
| azure_comms_event_id | string | Azure comms event identifier. |
| azure_comms_event_title | string | Azure comms event title. |
| azure_request_id | string | Azure request identifier. |
| bake_duration | real | Bake duration. |
| bake_start_time | datetime | Bake start time timestamp. |
| batch_host | bool | Boolean flag indicating whether batch host. |
| batch_id | long | Batch identifier. |
| batch_platform | string | Batch platform. |
| batch_sf | string | Batch sf. |
| begin_cycle_pending_upgrade_count | long | Number of begin cycle pending upgrade. |
| begin_cycle_pending_upgrade_size | long | Begin cycle pending upgrade size. |
| best_effort | bool | Boolean flag indicating whether best effort. |
| best_effort_wait_ms | real | Best effort wait ms in milliseconds. |
| best_effort_wait_per_ring_tag | string | Best effort wait per ring tag. |
| block | bool | Boolean flag indicating whether block. |
| breakpoint_id | string | Breakpoint identifier. |
| breakpoint_mode | string | Breakpoint mode. |
| build_autoselection_mode | string | Build autoselection mode. |
| build_branch_name | string | Build branch name. |
| build_branch_version | string | Build branch version. |
| build_location | string | Build location. |
| cache_event_type | string | Type classification for cache event. |
| caller | string | Caller. |
| caller_keys | string | Caller keys. |
| caller_state_machine_type | string | Type classification for caller state machine. |
| certificate_name | string | Certificate name. |
| changed_time | datetime | Changed time timestamp. |
| claimed_job_state | string | State value for claimed job. |
| claimed_timestamp | string | Claimed timestamp. |
| cleanup_stage | string | Cleanup stage. |
| cleanup_type | string | Type classification for cleanup. |
| client_address | string | Client address. |
| closed_window_app_upgrade_block_mode | string | Closed window app upgrade block mode. |
| closed_window_winfab_infra_block_mode | string | Closed window winfab infra block mode. |
| closed_window_winfab_upgrade_block_mode | string | Closed window winfab upgrade block mode. |
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| comms_stage | string | Comms stage. |
| communication_id | string | Communication identifier. |
| config_package_name | string | Config package name. |
| content | string | Content. |
| context_instance_name | string | Context instance name. |
| coordination_capacity | long | Coordination capacity. |
| current_ad_app_type_version | string | Current ad app type version. |
| current_app_param_key | string | Current app param key. |
| current_app_param_value | string | Current app param value. |
| current_application_type_version | string | Current application type version. |
| current_application_types | string | Current application types. |
| current_bake_duration | string | Current bake duration. |
| current_batch_priority | string | Current batch priority. |
| current_block_state | string | State value for current block. |
| current_cluster_capacity | real | Current cluster capacity. |
| current_cluster_remaining_capacity | real | Current cluster remaining capacity. |
| current_cluster_upgrade_capacity_buffer_count | long | Number of current cluster upgrade capacity buffer. |
| current_cluster_upgrade_capacity_buffer_size | real | Current cluster upgrade capacity buffer size. |
| current_code_version | string | Current code version. |
| current_config_version | string | Current config version. |
| current_deployment_window | string | Current deployment window. |
| current_error_count | string | Number of current error. |
| current_instance_parallelism | string | Current instance parallelism. |
| current_instance_size_parallelism | string | Current instance size parallelism. |
| current_jobs | string | Current jobs. |
| current_override_value | string | Current override value. |
| current_winfab_cluster_manifest_version | string | Current winfab cluster manifest version. |
| current_winfab_msi_version | string | Current winfab msi version. |
| currently_upgrading | long | Currently upgrading. |
| currnet_application_type_version | string | Currnet application type version. |
| customer_flighting_tag | string | Customer flighting tag. |
| customer_notification_properties | string | Customer notification properties. |
| cycle_id | string | Cycle identifier. |
| data | string | Data. |
| deadline | datetime | Deadline. |
| decided_start_time | datetime | Decided start time timestamp. |
| decided_start_time_local | datetime | Decided start time local. |
| degreeOfParallelism | long | Degree Of Parallelism. |
| denied_action_type | string | Type classification for denied action. |
| deployment_name | string | Deployment name. |
| deployment_pinning_info_id | long | Deployment pinning info identifier. |
| deployment_slot | string | Deployment slot. |
| deployment_tag | string | Deployment tag. |
| desirability | float | Desirability. |
| destinationAccountName | string | Destination Account Name. |
| destinationContainerName | string | Destination Container Name. |
| destinationDirectoryName | string | Destination Directory Name. |
| details | string | Details. |
| difference | string | Difference. |
| dng_id | string | Dng identifier. |
| does_match | bool | Boolean flag indicating whether does match. |
| drain_log | string | Drain log. |
| duration | real | Duration. |
| early_bake_triggered | bool | Boolean flag indicating whether early bake triggered. |
| effective_delta_mode | string | Effective delta mode. |
| elapsedTime | string | Elapsed Time. |
| elapsed_time_milliseconds | real | Elapsed duration in milliseconds. |
| enable_delta_health_evaluation | bool | Boolean flag indicating whether enable delta health evaluation. |
| end_time | datetime | End timestamp. |
| end_time_utc | datetime | End time utc. |
| environment_mapping | string | Environment mapping. |
| error_message | string | Error message. |
| error_number | string | SQL or platform error number. |
| estimated_duration_ms | real | Estimated duration ms in milliseconds. |
| event | string | Event name emitted by the component. |
| event_id | string | Event identifier. |
| event_time | string | Event time timestamp. |
| event_type | string | Type classification for event. |
| exception_message | string | Exception message. |
| exception_stack_trace | string | Exception stack trace. |
| exception_type | string | Type classification for exception. |
| exclude_tenant_repair_task_cancellation | string | Exclude tenant repair task cancellation. |
| extra_info | string | Extra info. |
| fabricClusterName | string | Fabric Cluster Name. |
| fabric_application_uri | string | Fabric application uri. |
| fabric_cluster_name | string | Fabric cluster name. |
| fabric_controller | string | Fabric controller. |
| failed_add | string | Failed add. |
| failed_remove | string | Failed remove. |
| favored_log | string | Favored log. |
| force | string | Force. |
| force_restart | bool | Boolean flag indicating whether force restart. |
| force_start | bool | Boolean flag indicating whether force start. |
| free | long | Free. |
| fsm_event | string | Fsm event. |
| fsm_instance_id | string | Fsm instance identifier. |
| fsm_version | long | Fsm version. |
| fuzzy_success_threshold | real | Fuzzy success threshold. |
| gc_memory_delta | real | Gc memory delta. |
| got_dng_id | bool | Got dng identifier. |
| he_variables | string | He variables. |
| health_check_retry_timeout | string | Health check retry timeout. |
| health_check_stable_duration | string | Health check stable duration. |
| health_check_wait_duration | string | Health check wait duration. |
| health_event_propery_name | string | Health event propery name. |
| health_event_propery_value | string | Health event propery value. |
| health_moving_avg | real | Health moving avg. |
| health_reports | string | Health reports. |
| health_state | string | State value for health. |
| hosted_service | string | Hosted service. |
| hosted_service_name | string | Hosted service name. |
| hosted_service_subscription_id | string | Hosted service subscription identifier. |
| hosted_services_names | string | Hosted services names. |
| id | string | identifier. |
| image_store_account_name | string | Image store account name. |
| image_store_container_name | string | Image store container name. |
| image_store_path | string | Image store path. |
| impact | string | Impact. |
| impact_action | string | Impact action. |
| impactful_job_status | string | Status value for impactful job. |
| in_workflow | bool | Boolean flag indicating whether in workflow. |
| incident_id | string | Incident identifier. |
| incoming_instances | string | Incoming instances. |
| infra_blocking_policies | string | Infra blocking policies. |
| infra_coordination_state | string | State value for infra coordination. |
| infra_job_action | string | Infra job action. |
| infra_metadata | string | Infra metadata. |
| infra_status | string | Status value for infra. |
| infrastructure_service_name_suffix | string | Infrastructure service name suffix. |
| infrastructure_service_uri | string | Infrastructure service uri. |
| input_ad_app_type_version | string | Input ad app type version. |
| input_app_param_key | string | Input app param key. |
| input_app_param_value | string | Input app param value. |
| instance | string | Instance. |
| instance_count | long | Number of instance. |
| inter_app_time_milliseconds | real | Inter app time in milliseconds. |
| internal_title | string | Internal title. |
| intra_app_time_milliseconds | real | Intra app time in milliseconds. |
| invocation_elapsed_time_milliseconds | real | Invocation elapsed time in milliseconds. |
| irsm_corresponding_property_value | string | Irsm corresponding property value. |
| isRecursive | bool | Boolean flag indicating whether Recursive. |
| isServerSideCopy | bool | Boolean flag indicating whether Server Side Copy. |
| is_aged_out | bool | Boolean flag indicating whether aged out. |
| is_in_test_zone | bool | Boolean flag indicating whether in test zone. |
| is_override_cleanable | bool | Boolean flag indicating whether override cleanable. |
| is_retired | bool | Boolean flag indicating whether retired. |
| is_stable_state | bool | Boolean flag indicating whether stable state. |
| iteration_id | string | Iteration identifier. |
| iteration_number | long | Iteration number. |
| job_exists | string | Job exists. |
| job_id | string | Job identifier. |
| job_mode | string | Job mode. |
| job_status | string | Status value for job. |
| justification | string | Justification. |
| keys | string | Keys. |
| kickoff_failed_count | real | Number of kickoff failed. |
| kickoff_failed_size | long | Kickoff failed size. |
| kickoff_in_cycle_count | long | Number of kickoff in cycle. |
| kickoff_in_cycle_size | long | Kickoff in cycle size. |
| kickoff_success_count | real | Number of kickoff success. |
| kickoff_success_size | long | Kickoff success size. |
| last_change | string | Last change. |
| last_error_at | datetime | Last error at. |
| last_healthy_at | datetime | Last healthy at. |
| last_overflow | datetime | Last overflow. |
| last_progress | datetime | Last progress. |
| last_retry_date | datetime | Last retry date. |
| last_sfrp_arm_deployment_failure | string | Last sfrp arm deployment failure. |
| last_state_change_time_utc | datetime | Last state change time utc. |
| last_state_changed_time | string | Last state changed time timestamp. |
| last_update_time | string | Last update time timestamp. |
| level | string | Level. |
| live_migration | bool | Boolean flag indicating whether live migration. |
| location | string | Location. |
| logical_database_id | string | Logical database identifier. |
| logical_database_name | string | Logical database name. |
| logical_uds_with_pending_infra | string | Logical uds with pending infra. |
| maintenance_id | string | Maintenance identifier. |
| maintenance_window_id | string | Maintenance window identifier. |
| max_notification_partition_size | long | Maximum notification partition size. |
| max_retry_attempts | long | Maximum retry attempts. |
| maximum_allowed | long | Maximum allowed. |
| message | string | Human-readable message text. |
| metadata | string | Metadata. |
| min_percent_cluster_remaining_capacity | long | Minimum percentage cluster remaining capacity. |
| min_publishing_window_size | string | Minimum publishing window size. |
| missed_notification_type | string | Type classification for missed notification. |
| monitoring_failure_count | real | Number of monitoring failure. |
| monitoring_failure_size | long | Monitoring failure size. |
| monitoring_remaining_apps_count | long | Number of monitoring remaining apps. |
| monitoring_remaining_apps_size | long | Monitoring remaining apps size. |
| monitoring_success_count | long | Number of monitoring success. |
| monitoring_success_size | long | Monitoring success size. |
| move_mode | string | Move mode. |
| name | string | Object or resource name. |
| new_application_types | string | New application types. |
| new_claimed_job | string | New claimed job. |
| new_claimed_job_list | string | New claimed job list. |
| new_cluster_manifest_version | string | New cluster manifest version. |
| new_deployment_variables_version | string | New deployment variables version. |
| new_jobs | string | New jobs. |
| new_metadata | string | New metadata. |
| new_phase | string | New phase. |
| new_repair_task_list | string | New repair task list. |
| new_state | string | State value for new. |
| new_throttle_setting | string | New throttle setting. |
| new_version | string | New version. |
| next_maintenance_window_end_time_utc | datetime | Next maintenance window end time utc. |
| next_maintenance_window_start_time_utc | datetime | Next maintenance window start time utc. |
| next_time_to_do_work_utc | datetime | Next time to do work utc. |
| next_time_to_publish_notifications | datetime | Next time to publish notifications. |
| next_ud | string | Next ud. |
| no_drain_reason | string | No drain reason. |
| node_id | string | Node identifier. |
| node_update_time | datetime | Node update time timestamp. |
| nodes | string | Nodes. |
| nodes_information | string | Nodes information. |
| not_ready_for_next_ud | string | Not ready for next ud. |
| notification_batch_id | string | Notification batch identifier. |
| notification_content | string | Notification content. |
| notification_id | string | Notification identifier. |
| notification_published_content | string | Notification published content. |
| notification_stage | string | Notification stage. |
| notification_success | bool | Boolean flag indicating whether notification success. |
| old_claimed_job_list | string | Old claimed job list. |
| old_cluster_manifest_version | string | Old cluster manifest version. |
| old_deployment_variables_version | string | Old deployment variables version. |
| old_jobs | string | Old jobs. |
| old_metadata | string | Old metadata. |
| old_phase | string | Old phase. |
| old_repair_task_list | string | Old repair task list. |
| old_state | string | State value for old. |
| old_throttle_setting | string | Old throttle setting. |
| old_version | string | Old version. |
| operation | string | Operation. |
| operation_status | string | Status value for operation. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| outgoing_instances | string | Outgoing instances. |
| override_age_days | long | Override age days. |
| override_insert_date_utc | datetime | Override insert date utc. |
| pacakge_path | string | Pacakge path. |
| package | string | Package. |
| package_validation_error_reports | string | Package validation error reports. |
| parameter_delta | string | Parameter delta. |
| pause_rollback_reason | string | Pause rollback reason. |
| payload | string | Payload. |
| payload_id | string | Payload identifier. |
| pending_node_count | long | Number of pending node. |
| pending_since | datetime | Pending since. |
| pending_winfab_cluster_manifest_version | string | Pending winfab cluster manifest version. |
| pending_winfab_msi_version | string | Pending winfab msi version. |
| phase | string | Phase. |
| planned_deployment_window | string | Planned deployment window. |
| platform_job_coordinator_state | string | State value for platform job coordinator. |
| previous_state_change | datetime | Previous state change. |
| process_id | long | Process identifier. |
| product_family | string | Product family. |
| publish_time | datetime | Publish time timestamp. |
| publishing_delay | string | Publishing delay. |
| publishing_partition_frequency | string | Publishing partition frequency. |
| publishing_partition_id | long | Publishing partition identifier. |
| query_method | string | Query method. |
| reason | string | Reason. |
| reference_fabric_cluster | string | Reference fabric cluster. |
| remove_application_type_phase | string | Remove application type phase. |
| removed_overrides | string | Removed overrides. |
| repair_action | string | Repair action. |
| repair_task_approved | string | Repair task approved. |
| repair_task_id | string | Repair task identifier. |
| repair_task_state | string | State value for repair task. |
| repair_tasks_exist | string | Repair tasks exist. |
| request_content | string | Request content. |
| request_id | string | Request identifier used to correlate the operation. |
| request_params | string | Request params. |
| resource_group_name | string | Resource group name. |
| resource_status | string | Status value for resource. |
| response_body | string | Response body. |
| response_context | string | Response context. |
| result | string | Result. |
| retry_cancelled_count | long | Number of retry cancelled. |
| retry_count | long | Number of retry. |
| retry_poke_cooling_period_met | bool | Boolean flag indicating whether retry poke cooling period met. |
| revised_upgrade_policy | string | Revised upgrade policy. |
| role_instance | string | Role instance. |
| role_instances | string | Role instances. |
| rollback_deployment_variables_version | string | Rollback deployment variables version. |
| rollback_reason | string | Rollback reason. |
| rollback_version | string | Rollback version. |
| rollforward_deployment_variables_version | string | Rollforward deployment variables version. |
| rollforward_version | string | Rollforward version. |
| rollout_failure | string | Rollout failure. |
| rollout_key | string | Rollout key. |
| rollout_safety_mode | string | Rollout safety mode. |
| row_count | long | Number of row. |
| rows_count | long | Number of rows. |
| scenario_id | string | Scenario identifier. |
| scenario_name | string | Scenario name. |
| scheduled_action | string | Scheduled action. |
| scheduled_close_time | datetime | Scheduled close time timestamp. |
| scheduled_time | datetime | Scheduled time timestamp. |
| score_if_unwise | real | Score if unwise. |
| searchPattern | string | Search Pattern. |
| section_name | string | Section name. |
| service_manifest_name | string | Service manifest name. |
| service_name | string | Service name. |
| sessionName | string | Session Name. |
| setting_name | string | Setting name. |
| sfrp_arm_deployment_status | string | Status value for sfrp arm deployment. |
| sfrp_arm_template_path | string | Sfrp arm template path. |
| sfrp_arm_template_version | string | Sfrp arm template version. |
| sfrp_linked_template_parameters_path | string | Sfrp linked template parameters path. |
| shutdown_delay | string | Shutdown delay. |
| slice_fail_count | real | Number of slice fail. |
| slice_percentage | real | Slice pe percentage. |
| slice_size | real | Slice size. |
| slice_sucess_count | real | Number of slice sucess. |
| snapshot_id | string | Snapshot identifier. |
| source | string | Source. |
| sourceAccountName | string | Source Account Name. |
| sourceContainerName | string | Source Container Name. |
| sourceDirectoryName | string | Source Directory Name. |
| source_id | string | Source identifier. |
| sql_instance_name | string | SQL instance name. |
| stable_health_duration | real | Stable health duration. |
| stack_trace | string | Stack trace. |
| stale_application_types | string | Stale application types. |
| start_method | string | Start method. |
| start_time | datetime | Start timestamp. |
| start_time_utc | datetime | Start time utc. |
| state | string | Current lifecycle or health state. |
| state_machine_type | string | Type classification for state machine. |
| status | string | Current status reported by the component. |
| step | string | Step. |
| submit_time_jobs | string | Submit time jobs. |
| subscriptions | string | Subscriptions. |
| success | bool | Boolean flag indicating whether success. |
| synchronized | bool | Boolean flag indicating whether synchronized. |
| synchronized_uds | string | Synchronized uds. |
| system_cpu_time_milliseconds | real | System CPU time in milliseconds. |
| target_application_type_version | string | Target application type version. |
| target_block_state | string | State value for target block. |
| target_cluster_manifest_version | string | Target cluster manifest version. |
| target_code_version | string | Target code version. |
| target_config_version | string | Target config version. |
| target_deployment_variables_version | string | Target deployment variables version. |
| target_ring | string | Target ring. |
| target_rollout_mode | string | Target rollout mode. |
| target_stable_health_duration | real | Target stable health duration. |
| target_state | string | State value for target. |
| target_version | string | Target version. |
| text | string | Text. |
| threshold_exceeded | bool | Boolean flag indicating whether threshold exceeded. |
| time_left_to_timeout | real | Time left to timeout. |
| total_instances | long | Total instances. |
| transaction_id | string | Transaction identifier. |
| ud | string | Ud. |
| ud_id | string | Ud identifier. |
| unblock_action | string | Unblock action. |
| unhealthy_evaluations | string | Unhealthy evaluations. |
| updating_upgrade_apps_count | long | Number of updating upgrade apps. |
| updating_upgrade_apps_size | long | Updating upgrade apps size. |
| upgrade_completed_count | real | Number of upgrade completed. |
| upgrade_completed_size | long | Upgrade completed size. |
| upgrade_description | string | Upgrade description. |
| upgrade_domain | string | Upgrade domain. |
| upgrade_domain_timeout | string | Upgrade domain timeout. |
| upgrade_failure_action | string | Upgrade failure action. |
| upgrade_key | string | Upgrade key. |
| upgrade_mode | string | Upgrade mode. |
| upgrade_order | string | Upgrade order. |
| upgrade_policy | string | Upgrade policy. |
| upgrade_progress | string | Upgrade progress. |
| upgrade_state | string | State value for upgrade. |
| upgrade_timeout | string | Upgrade timeout. |
| upgraded_instances | long | Upgraded instances. |
| used | long | Used. |
| user_cpu_time_milliseconds | real | User CPU time in milliseconds. |
| user_name | string | User name. |
| validation_policy | string | Validation policy. |
| value_source | string | Value source. |
| versions_collected | long | Versions collected. |
| virtual_job_name | string | Virtual job name. |
| virtual_job_state | string | State value for virtual job. |
| virtual_jobs | string | Virtual jobs. |
| window_scheduler | string | Window scheduler. |
| winfab_cluster_manifest_path | string | Winfab cluster manifest path. |
| winfab_cluster_name | string | Winfab cluster name. |
| winfab_infra_job_list | string | Winfab infra job list. |
| winfab_infra_new_status | string | Status value for winfab infra new. |
| winfab_infra_old_status | string | Status value for winfab infra old. |
| winfab_msi_path | string | Winfab msi path. |
| winfab_rollout_new_status | string | Status value for winfab rollout new. |
| winfab_upgrade_cluster_manifest_version | string | Winfab upgrade cluster manifest version. |
| winfab_upgrade_msi_version | string | Winfab upgrade msi version. |
| winfab_upgrade_target_block_mode | string | Winfab upgrade target block mode. |
| wise_score | real | Wise score. |
| work_item_id | string | Work item identifier. |
| work_status | string | Status value for work. |
| workflow_uri | string | Workflow uri. |

## MonSocrates — Socrates

**Purpose**: Socrates. Used to investigate platform automation, deployment, cluster configuration, and provisioning workflows. Referenced in MI template areas: availability.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| ActorBsn | long | Actor Bsn. |
| ActorCatchupRate | long | Actor Catchup Rate. |
| ActorDistance | long | Actor Distance. |
| ActorId | string | Actor Id. |
| ActorNodeId | long | Actor Node Id. |
| ActorRole | string | Actor Role. |
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| CatchupRate | long | Catchup Rate. |
| CurrentBsn | long | Current Bsn. |
| CurrentLsn | string | Current Lsn. |
| Distance | long | Distance. |
| Id | string | Id identifier. |
| LogicalDatabaseId | string | Logical Database Id. |
| MaxLogThroughput | long | Max Log Throughput. |
| MetricNamespace | string | Metric Namespace. |
| MonitoringAccount | string | Monitoring Account. |
| NewThrottle | long | New Throttle. |
| NodeId | long | Node Id. |
| PartitionId | string | Partition Id. |
| PreviousThrottle | long | Previous Throttle. |
| PrimaryEoLBsn | long | Primary Eo LBsn. |
| PrimaryLogRate | long | Primary Log Rate. |
| Role | string | Role. |
| SampleDuration | long | Sample Duration. |
| SiblingDistance | long | Sibling Distance. |
| SiblingId | string | Sibling Id. |
| WaitType | string | Wait Type. |
| XlogUnresponsiveDuration | long | Xlog Unresponsive Duration. |
| accumulated_count | long | Number of accumulated. |
| accumulation | long | Accumulation. |
| action | string | Action. |
| actor | string | Actor. |
| actor_distance_mb | long | Actor distance mb. |
| actor_id | string | Actor identifier. |
| additional_buffer_reported_mb | long | Additional buffer reported mb. |
| address_endpoint_1_0 | string | Address endpoint 1 0. |
| address_endpoint_1_1 | string | Address endpoint 1 1. |
| adjusted_lz_iter_read_size | long | Adjusted lz iter read size. |
| after_grow_free_pages | long | After grow free pages. |
| after_grow_free_segments | long | After grow free segments. |
| after_grow_size_in_pages | long | After grow size in pages. |
| after_sparse_size | long | After sparse size. |
| allocated_database_space_in_Gb | long | Allocated database space in Gb. |
| allocated_kb | long | Allocated kb. |
| allocated_size | long | Allocated size. |
| allocation_unit_id | long | Allocation unit identifier. |
| analysis_lsn | string | Analysis lsn. |
| analyze_lock_acquire_time_us | long | Analyze lock acquire time us. |
| analyze_lsn | string | Analyze lsn. |
| analyze_record_count | long | Number of analyze record. |
| analyze_record_time | long | Analyze record time timestamp. |
| applied_bsn | long | Applied bsn. |
| applied_lsn_str | string | Applied lsn str. |
| associated_object_id | long | Associated object identifier. |
| async_read_duration_in_microsec | long | Async read duration in microsec. |
| attach_activity_id | string | Attach activity identifier. |
| attach_activity_id_xfer | string | Attach activity id xfer. |
| attempt_number | long | Attempt number. |
| available_database_space_in_Gb | long | Available database space in Gb. |
| available_zones_count | long | Number of available zones. |
| avg_distance | long | Average distance. |
| avoided_retraversal_future_page | long | Avoided retraversal future page. |
| avoided_retraversal_sysxact | long | Avoided retraversal sysxact. |
| bad_pages | long | Bad pages. |
| before_grow_free_pages | long | Before grow free pages. |
| before_grow_free_segments | long | Before grow free segments. |
| before_grow_size_in_pages | long | Before grow size in pages. |
| before_sparse_size | long | Before sparse size. |
| begin_lsn | string | Begin lsn. |
| bg_thread_total_time_ms | long | Bg thread total time ms in milliseconds. |
| bits_set_due_to_create_file | long | Bits set due to create file. |
| bits_set_due_to_grow_file | long | Bits set due to grow file. |
| bits_validated | long | Bits validated. |
| block_id | long | Block identifier. |
| block_ps_due_to_lc_seed | long | Block ps due to lc seed. |
| block_size | long | Block size. |
| blocks_unlinked | long | Blocks unlinked. |
| blocks_unlinked_0 | long | Blocks unlinked 0. |
| blocks_unlinked_gt_1000 | long | Blocks unlinked gt 1000. |
| blocks_unlinked_le_10 | long | Blocks unlinked le 10. |
| blocks_unlinked_le_100 | long | Blocks unlinked le 100. |
| blocks_unlinked_le_1000 | long | Blocks unlinked le 1000. |
| blocks_unlinked_le_2 | long | Blocks unlinked le 2. |
| blocks_unlinked_le_5 | long | Blocks unlinked le 5. |
| blocks_unlinked_le_50 | long | Blocks unlinked le 50. |
| blocks_unpacked | long | Blocks unpacked. |
| boot_page_lsn | string | Boot page lsn. |
| broker_blocks_unlinked | long | Broker blocks unlinked. |
| broker_full | long | Broker full. |
| broker_inserts_above_max_allowed | long | Broker inserts above max allowed. |
| broker_max | long | Broker max. |
| broker_max_allowed | long | Broker max allowed. |
| broker_min | long | Broker min. |
| broker_pages_unlinked | long | Broker pages unlinked. |
| bsn | long | Bsn. |
| bsn_from | long | Bsn from. |
| bsn_io_pool_max_used_count | long | Number of bsn I/O pool max used. |
| bsn_requested | long | Bsn requested. |
| bsn_to | long | Bsn to. |
| bsns_per_dirty_pages_mapping | real | Bsns per dirty pages mapping. |
| btree_readsec_telemetry_location | long | Btree readsec telemetry location. |
| bucket_hits | long | Bucket hits. |
| bucket_hits_00 | long | Bucket hits 00. |
| bucket_hits_01 | long | Bucket hits 01. |
| bucket_hits_02 | long | Bucket hits 02. |
| bucket_hits_03 | long | Bucket hits 03. |
| bucket_hits_04 | long | Bucket hits 04. |
| bucket_hits_05 | long | Bucket hits 05. |
| bucket_hits_06 | long | Bucket hits 06. |
| bucket_hits_07 | long | Bucket hits 07. |
| bucket_hits_08 | long | Bucket hits 08. |
| bucket_hits_09 | long | Bucket hits 09. |
| bucket_hits_10 | long | Bucket hits 10. |
| bucket_hits_11 | long | Bucket hits 11. |
| bucket_hits_12 | long | Bucket hits 12. |
| bucket_hits_13 | long | Bucket hits 13. |
| bucket_hits_14 | long | Bucket hits 14. |
| bucket_hits_15 | long | Bucket hits 15. |
| bucket_hits_16 | long | Bucket hits 16. |
| bucket_hits_17 | long | Bucket hits 17. |
| bucket_hits_18 | long | Bucket hits 18. |
| bucket_hits_19 | long | Bucket hits 19. |
| bucket_hits_20 | long | Bucket hits 20. |
| bucket_hits_21 | long | Bucket hits 21. |
| bucket_hits_22 | long | Bucket hits 22. |
| bucket_hits_Total | long | Bucket hits Total. |
| bucket_position | long | Bucket position. |
| bucket_range | long | Bucket range. |
| buf_pair | string | Buf pair. |
| buffer_size_pages | long | Buffer size pages. |
| bufpairs_validated | long | Bufpairs validated. |
| bytesDiff | long | Bytes Diff. |
| bytes_grown | long | Bytes grown. |
| bytes_read | long | Bytes read. |
| bytes_recvd_total | long | Bytes recvd total. |
| bytes_sent_total | long | Bytes sent total. |
| bytes_to_shrink | long | Bytes to shrink. |
| call_site | string | Call site. |
| call_stack | string | Call stack. |
| callfunction | string | Callfunction. |
| callsite | string | Callsite. |
| callstack_rva | string | Callstack rva. |
| catch_up_distance_bytes | long | Catch up distance size in bytes. |
| checkpoint_checksum_read_io_error_count | long | Number of checkpoint checksum read I/O error. |
| checkpoint_error_count | long | Number of checkpoint error. |
| checkpoint_failed_read_io_error_count | long | Number of checkpoint failed read I/O error. |
| checkpoint_fault_inject_count | long | Number of checkpoint fault inject. |
| checkpoint_id | long | Checkpoint identifier. |
| checkpoint_indoubt_read_io_error_count | long | Number of checkpoint indoubt read I/O error. |
| checkpoint_lsn | string | Checkpoint lsn. |
| checkpoint_lsn_source | string | Checkpoint lsn source. |
| checkpoint_no_available_shared_io_buffers | long | Checkpoint no available shared I/O buffers. |
| checkpoint_page_id_io_error_count | long | Number of checkpoint page id I/O error. |
| checkpoint_progress_stalled_count | long | Number of checkpoint progress stalled. |
| checkpoint_read_io_error | long | Checkpoint read I/O error. |
| checkpoint_retries_after_stream_empty | long | Checkpoint retries after stream empty. |
| checkpoint_retry_buffer_pool_read | long | Checkpoint retry buffer pool read. |
| checkpoint_retry_latch_error | long | Checkpoint retry latch error. |
| checkpoint_retry_latch_success | long | Checkpoint retry latch success. |
| checkpoint_retry_read_io_error | long | Checkpoint retry read I/O error. |
| checkpoint_retry_read_io_success | long | Checkpoint retry read I/O success. |
| checkpoint_scan_end | long | Checkpoint scan end. |
| checkpoint_skipped | long | Checkpoint skipped. |
| checkpoint_stale_page_io_error_count | long | Number of checkpoint stale page I/O error. |
| checkpoint_stream_empty | long | Checkpoint stream empty. |
| checkpoint_task_aborted_count | long | Number of checkpoint task aborted. |
| checkpoint_wait_failure_count | long | Number of checkpoint wait failure. |
| checkpoint_write_io_error | long | Checkpoint write I/O error. |
| checkptBsn | long | Checkpt Bsn. |
| circuit_index | long | Circuit index. |
| ckpt_bsn_to_report | long | Ckpt bsn to report. |
| ckpt_calculated_bsn_to_report | long | Ckpt calculated bsn to report. |
| client_id | string | Client identifier. |
| client_node_id | long | Client node identifier. |
| client_role | string | Client role. |
| code_package_start_time | long | Code package start time timestamp. |
| code_package_version | string | Code package version. |
| cold_page_count_from_connection | long | Cold page count from connection. |
| cold_page_count_in_rbpex | long | Cold page count in rbpex. |
| collect_current_thread_id | long | Collect current thread identifier. |
| complete_io_after_valid_data | long | Complete I/O after valid data. |
| complete_io_before_valid_data | long | Complete I/O before valid data. |
| complete_io_count_invocation | long | Complete I/O count invocation. |
| complete_io_failure | long | Complete I/O failure. |
| complete_io_page_reissued | long | Complete I/O page reissued. |
| complete_io_page_stitched | long | Complete I/O page stitched. |
| complete_io_parse_error | long | Complete I/O parse error. |
| complete_io_retry_no_data | long | Complete I/O retry no data. |
| complete_io_total_time | long | Complete I/O total time timestamp. |
| completion_status | long | Status value for completion. |
| component | string | Component. |
| compute_flush_lsn | string | Compute flush lsn. |
| concurrent_completion | long | Concurrent completion. |
| conn_abort_close_requested | long | Conn abort close requested. |
| conn_abort_thread_cancel | long | Conn abort thread cancel. |
| conn_active_endpoint_marked_as_duplicate | long | Conn active endpoint marked as duplicate. |
| conn_active_endpoint_soft_retry_qos | long | Conn active endpoint soft retry qos. |
| conn_bind_by_name_attempt | long | Conn bind by name attempt. |
| conn_bind_by_name_success | long | Conn bind by name success. |
| conn_bind_by_stream_attempt | long | Conn bind by stream attempt. |
| conn_bind_by_stream_success | long | Conn bind by stream success. |
| conn_circuit0_msg_count | long | Number of conn circuit0 msg. |
| conn_circuit1_msg_count | long | Number of conn circuit1 msg. |
| conn_circuit_msg_count | long | Number of conn circuit msg. |
| conn_closed_stale | long | Conn closed stale. |
| conn_complete_response_ok | long | Conn complete response ok. |
| conn_connecting | long | Conn connecting. |
| conn_copy_out_failure | long | Conn copy out failure. |
| conn_disconnected | long | Conn disconnected. |
| conn_dispatch_async_request_failure | long | Conn dispatch async request failure. |
| conn_dispatch_request | long | Conn dispatch request. |
| conn_dispatch_response | long | Conn dispatch response. |
| conn_dual_mode | long | Conn dual mode. |
| conn_fail_fast_server | long | Conn fail fast server. |
| conn_failure_to_acquire_read_lock | long | Conn failure to acquire read lock. |
| conn_failure_to_acquire_readlock | long | Conn failure to acquire readlock. |
| conn_failure_to_connect | long | Conn failure to connect. |
| conn_failure_to_connect_qos | long | Conn failure to connect qos. |
| conn_failure_to_connect_qos_timeout | long | Conn failure to connect qos timeout. |
| conn_failure_to_connect_timeout | long | Conn failure to connect timeout. |
| conn_flow_controlled | long | Conn flow controlled. |
| conn_flow_controlled_timeout | long | Conn flow controlled timeout. |
| conn_fuzzed_send_recv_complete | long | Conn fuzzed send recv complete. |
| conn_generation_mismatch | long | Conn generation mismatch. |
| conn_id | string | Conn identifier. |
| conn_incompatible_server | long | Conn incompatible server. |
| conn_invalid_msg_format | long | Conn invalid msg format. |
| conn_invalid_size | long | Conn invalid size. |
| conn_invalid_type | long | Type classification for conn invalid. |
| conn_invalid_version | long | Conn invalid version. |
| conn_local_completion_won | long | Conn local completion won. |
| conn_log_replica_page_server_redo_behind | long | Conn log replica page server redo behind. |
| conn_log_replica_secondary_lagging_rebound | long | Conn log replica secondary lagging rebound. |
| conn_log_replica_secondary_lagging_redirected_to_primary | long | Conn log replica secondary lagging redirected to primary. |
| conn_max_resends_reached | long | Conn max resends reached. |
| conn_msg_discarded_injection | long | Conn msg discarded injection. |
| conn_msg_lost_by_ucs | long | Conn msg lost by UCS. |
| conn_msh_failure | long | Conn msh failure. |
| conn_qos_both_completed | long | Conn qos both completed. |
| conn_qos_both_pending | long | Conn qos both pending. |
| conn_qos_both_permanent_error | long | Conn qos both permanent error. |
| conn_qos_both_requested_retry | long | Conn qos both requested retry. |
| conn_qos_both_transient_error | long | Conn qos both transient error. |
| conn_qos_new_probe_error | long | Conn qos new probe error. |
| conn_qos_one_completed_waits | long | Conn qos one completed waits. |
| conn_qos_one_completed_wins | long | Conn qos one completed wins. |
| conn_qos_one_pending_one_permanent_error | long | Conn qos one pending one permanent error. |
| conn_qos_one_pending_one_success | long | Conn qos one pending one success. |
| conn_qos_one_pending_one_transient_error | long | Conn qos one pending one transient error. |
| conn_qos_one_success_one_permanent_error | long | Conn qos one success one permanent error. |
| conn_qos_one_success_one_transient_error | long | Conn qos one success one transient error. |
| conn_qos_one_transient_one_permanent_error | long | Conn qos one transient one permanent error. |
| conn_qos_probe_error | long | Conn qos probe error. |
| conn_qos_saw_dup_address | long | Conn qos saw dup address. |
| conn_rebalance_endpoint | long | Conn rebalance endpoint. |
| conn_received_invalid_type | long | Type classification for conn received invalid. |
| conn_remote_completion_won | long | Conn remote completion won. |
| conn_request_count | long | Number of conn request. |
| conn_resend_downgraded_msg | long | Conn resend downgraded msg. |
| conn_resend_soft_retry_msg | long | Conn resend soft retry msg. |
| conn_resend_stalled_msg | long | Conn resend stalled msg. |
| conn_retry_demanded_by_server | long | Conn retry demanded by server. |
| conn_sent_auto_downgraded_msg | long | Conn sent auto downgraded msg. |
| conn_server_retry_duration_ms | long | Conn server retry duration ms in milliseconds. |
| conn_server_side_fail_fast_on_wait | long | Conn server side fail fast on wait. |
| conn_single_mode | long | Conn single mode. |
| conn_skipped_rebalance_target_unhealthy | long | Conn skipped rebalance target unhealthy. |
| conn_soft_retry_demanded_by_server | long | Conn soft retry demanded by server. |
| conn_stalled_count | long | Number of conn stalled. |
| conn_stalled_found_active | long | Conn stalled found active. |
| conn_stalled_resend_failed | long | Conn stalled resend failed. |
| conn_wait_for_connection | long | Conn wait for connection. |
| conn_wait_for_connection_retry | long | Conn wait for connection retry. |
| consumer_id | long | Consumer identifier. |
| consumer_name | string | Consumer name. |
| content_length | long | Content length. |
| continuous_redo_log_redone_count | long | Number of continuous redo log redone. |
| copied | long | Copied. |
| correlation_id | string | Correlation identifier used across components. |
| count | long | Number of count. |
| count_failed_notifications | long | Number of count failed notifications. |
| count_modified_pages_in_io | long | Number of count modified pages in I/O. |
| cur_pair_prisnap_name | string | Cur pair prisnap name. |
| cur_pair_secsnap_name | string | Cur pair secsnap name. |
| cur_pair_state | long | State value for cur pair. |
| cur_pair_state_desc | string | Cur pair state desc. |
| curr_event | string | Curr event. |
| current_bsn | long | Current bsn. |
| current_database_max_size_in_Gb | long | Current database max size in Gb. |
| current_database_size_in_Gb | long | Current database size in Gb. |
| current_dirty_pages_map_to_bsn | long | Current dirty pages map to bsn. |
| current_file_size | long | Current file size. |
| current_foreign_apply_bsn | long | Current foreign apply bsn. |
| current_full | long | Current full. |
| current_lsn | string | Current lsn. |
| current_page_type | string | Type classification for current page. |
| current_safe_vlf | long | Current safe vlf. |
| current_total_dirty_pages | long | Current total dirty pages. |
| current_wb_log_dist_in_kb | long | Current wb log dist in kb. |
| database_id | long | Database identifier. |
| database_name | string | Database name. |
| db_id | long | Database identifier. |
| db_name | string | Database name. |
| dbid | string | Dbid. |
| defer_dealloc_marked_page_count | long | Number of defer dealloc marked page. |
| defer_dealloc_pages_deallocated_by_gc_count | long | Number of defer dealloc pages deallocated by gc. |
| defer_dealloc_pages_visited_by_gc_count | long | Number of defer dealloc pages visited by gc. |
| destage_blob_type | string | Type classification for destage blob. |
| destage_bsn | long | Destage bsn. |
| destage_log_eol_read_count | long | Number of destage log eol read. |
| destage_log_eol_read_ms | long | Destage log eol read ms in milliseconds. |
| destage_log_from_broker | long | Destage log from broker. |
| destage_log_from_lc | long | Destage log from lc. |
| destage_log_from_lt | long | Destage log from lt. |
| destage_log_from_lz | long | Destage log from lz. |
| destage_log_from_pool | long | Destage log from pool. |
| destage_log_read_time_ms | long | Destage log read time ms in milliseconds. |
| destage_log_register_vlf_time_ms | long | Destage log register vlf time ms in milliseconds. |
| destage_log_stall_due_to_queue_depth | long | Destage log stall due to queue depth. |
| destage_log_total_time_ms | long | Destage log total time ms in milliseconds. |
| destage_log_zeroing | long | Destage log zeroing. |
| destaged_block_total_bytes_hardened | long | Destaged block total size in bytes hardened. |
| destaged_block_total_bytes_issued | long | Destaged block total size in bytes issued. |
| device_write_offset | long | Device write offset. |
| dirty_page_lsn | string | Dirty page lsn. |
| disk_io_completed | long | Disk I/O completed. |
| distance_bucket_kb | long | Distance bucket kb. |
| distance_hits_00 | long | Distance hits 00. |
| distance_hits_01 | long | Distance hits 01. |
| distance_hits_02 | long | Distance hits 02. |
| distance_hits_03 | long | Distance hits 03. |
| distance_hits_04 | long | Distance hits 04. |
| distance_hits_05 | long | Distance hits 05. |
| distance_hits_06 | long | Distance hits 06. |
| distance_hits_07 | long | Distance hits 07. |
| distance_hits_08 | long | Distance hits 08. |
| distance_hits_09 | long | Distance hits 09. |
| distance_hits_10 | long | Distance hits 10. |
| distance_hits_11 | long | Distance hits 11. |
| distance_hits_12 | long | Distance hits 12. |
| distance_hits_13 | long | Distance hits 13. |
| distance_hits_14 | long | Distance hits 14. |
| distance_hits_15 | long | Distance hits 15. |
| distance_hits_total | long | Distance hits total. |
| distance_map_type | string | Type classification for distance map. |
| drain_io_count_invocation | long | Drain I/O count invocation. |
| drain_io_total_time | long | Drain I/O total time timestamp. |
| dropped_blocks | long | Dropped blocks. |
| duration | long | Duration. |
| duration_in_ms | long | Duration in ms in milliseconds. |
| duration_ms | long | Duration in milliseconds. |
| duration_seconds | long | Duration seconds. |
| egress_validator_inserted | long | Egress validator inserted. |
| egress_validator_not_found_in_map | long | Egress validator not found in map. |
| egress_validator_skip_wraparound | long | Egress validator skip wraparound. |
| egress_validator_verified_checksum | long | Egress validator verified checksum. |
| egress_validator_verified_size | long | Egress validator verified size. |
| elapsed_ms | long | Elapsed ms in milliseconds. |
| elapsed_time_in_millisec | long | Elapsed time in millisec. |
| elapsed_time_ms | long | Elapsed time ms in milliseconds. |
| enabled | bool | Boolean flag indicating whether enabled. |
| encryption_scan_completion_lsn | string | Encryption scan completion lsn. |
| end_bsn_id | long | End bsn identifier. |
| end_of_log_bsn | long | End of log bsn. |
| end_of_log_lsn | string | End of log lsn. |
| end_page_id | long | End page identifier. |
| ending_bit | long | Ending bit. |
| endpoint_condition_from | string | Endpoint condition from. |
| endpoint_condition_to | string | Endpoint condition to. |
| endpoint_index | long | Endpoint index. |
| eol_bsn | long | Eol bsn. |
| eol_lsn | string | Eol lsn. |
| error | long | Error text captured for the event or operation. |
| error_code | long | Numeric error code for the failure or event. |
| error_number | long | SQL or platform error number. |
| error_state | long | State value for error. |
| estimated_remaining_time_sec | long | Estimated remaining time sec. |
| evaluate_foreigncheckpoint_count | long | Number of evaluate foreigncheckpoint. |
| evaluate_foreigncheckpoint_time | long | Evaluate foreigncheckpoint time timestamp. |
| evaluation_threshold | long | Evaluation threshold. |
| event | string | Event name emitted by the component. |
| eviction_phase_runtime_ms | long | Eviction phase runtime ms in milliseconds. |
| eviction_routine_runtime_ms | long | Eviction routine runtime ms in milliseconds. |
| eviction_scan_hit_rate | real | Eviction scan hit rate. |
| exclusive | bool | Boolean flag indicating whether exclusive. |
| execution_status | long | Status value for execution. |
| expected_file_size_kb | long | Expected file size kb. |
| extra_hint_bsn_inclusive | long | Extra hint bsn inclusive. |
| fabric_replica_id | long | Fabric replica identifier. |
| failed_alloc_reclaim_or_delete | long | Failed alloc reclaim or delete. |
| failed_commit | long | Failed commit. |
| failed_delete_workitem_found | long | Failed delete workitem found. |
| failed_get_hk_row_delete_page | long | Failed get hk row delete page. |
| failed_get_hk_row_reclaim_page | long | Failed get hk row reclaim page. |
| failed_grow_zones | long | Failed grow zones. |
| failed_io_count | long | Number of failed I/O. |
| failed_lazy_commit | long | Failed lazy commit. |
| failed_physical_shrink_count | long | Number of failed physical shrink. |
| failed_read_page_index | long | Failed read page index. |
| failed_reads_count | long | Number of failed reads. |
| failed_rebinds | long | Failed rebinds. |
| failed_reclaim_or_delete_page | long | Failed reclaim or delete page. |
| failed_reclaim_or_delete_tx | long | Failed reclaim or delete tx. |
| failed_reclaim_tx | long | Failed reclaim tx. |
| failed_row_alloc_reclaim_page | long | Failed row alloc reclaim page. |
| failed_to_alloc_driver_mem | long | Failed to alloc driver memory. |
| failed_to_enqueue_task | long | Failed to enqueue task. |
| failed_workitem_found | long | Failed workitem found. |
| failed_workitem_on_locator_release | long | Failed workitem on locator release. |
| failed_xlog_prop_requests | long | Failed xlog prop requests. |
| failover_logblock_timestamp | string | Failover logblock timestamp. |
| failover_signature | long | Failover signature. |
| failure_message | string | Failure message. |
| fast_return_on_misaligned_read_in_tos | long | Fast return on misaligned read in tos. |
| fault_injection_count | long | Number of fault injection. |
| fault_injection_physical_shrink_count | long | Number of fault injection physical shrink. |
| fault_report_threshold | long | Fault report threshold. |
| fcb_type | string | Type classification for fcb. |
| file_growth_supported | bool | Boolean flag indicating whether file growth supported. |
| file_handle | string | File handle. |
| file_id | long | File identifier. |
| file_index | long | File index. |
| file_offset | long | File offset. |
| file_path | string | File path. |
| file_path_hash | string | File path hash. |
| file_pos | long | File pos. |
| file_size | long | File size. |
| fileid | long | Fileid. |
| first_begin_lsn | string | First begin lsn. |
| first_bucket_time | datetime | First bucket time timestamp. |
| first_dirty_page_beyond_local_file_size | long | First dirty page beyond local file size. |
| first_file_name | string | First file name. |
| first_incomplete_vlf | long | First incomplete vlf. |
| first_invalid_block | long | First invalid block. |
| first_name | string | First name. |
| first_page_in_io | long | First page in I/O. |
| first_valid_page | long | First valid page. |
| first_vlf | long | First vlf. |
| first_vlf_id | long | First vlf identifier. |
| flush_block | long | Flush block. |
| flush_bsn | long | Flush bsn. |
| flush_lsn | string | Flush lsn. |
| foreign_file1 | string | Foreign file1. |
| foreign_file2 | string | Foreign file2. |
| foreign_file_count | long | Number of foreign file. |
| foreign_file_id | long | Foreign file identifier. |
| foreign_file_path | string | Foreign file path. |
| foreign_redo_lsn | string | Foreign redo lsn. |
| foreign_redo_wait_in_microsec | long | Foreign redo wait in microsec. |
| free_extents_count_for_sysfile1 | long | Free extents count for sysfile1. |
| free_page_locator_count | long | Number of free page locator. |
| free_pages | long | Free pages. |
| free_pages_in_first | long | Free pages in first. |
| free_pages_in_second | long | Free pages in second. |
| free_pages_skipped | long | Free pages skipped. |
| free_segment_locator_count | long | Number of free segment locator. |
| free_shrink_page_locator_count | string | Number of free shrink page locator. |
| from_bsn | long | From bsn. |
| from_size_in_pages | long | From size in pages. |
| full_page_stride_scanned | long | Full page stride scanned. |
| function | string | Function. |
| function_name | string | Function name. |
| future_page_from_page_server | long | Future page from page server. |
| gap_filler_extra_hint_beyond_max_flushed | long | Gap filler extra hint beyond max flushed. |
| gap_filler_fill_from_lz | long | Gap filler fill from lz. |
| gap_filler_no_gaps | long | Gap filler no gaps. |
| gap_filler_wait_failure | long | Gap filler wait failure. |
| gap_filler_wait_success | long | Gap filler wait success. |
| gap_filler_wait_to_fill | long | Gap filler wait to fill. |
| generation_id | long | Generation identifier. |
| get_iterator_retry_count | long | Number of get iterator retry. |
| get_lock_complete_count | long | Number of get lock complete. |
| get_lock_complete_max_time | long | Get lock complete max time timestamp. |
| get_lock_complete_total_time | long | Get lock complete total time timestamp. |
| grow_e2e_timer | long | Grow e2e timer. |
| grow_size_pages | long | Grow size pages. |
| growth_id | long | Growth identifier. |
| has_deferred_file_growth | long | Boolean flag indicating whether deferred file growth. |
| has_vlf_info | bool | Boolean flag indicating whether has vlf info. |
| hit_after_enqueue | bool | Boolean flag indicating whether hit after enqueue. |
| hits | long | Hits. |
| hobt_id | long | Hobt identifier. |
| hot_page_count_from_connection | long | Hot page count from connection. |
| hot_pages_in_rbpex | long | Hot pages in rbpex. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| hr | long | Hr. |
| hresult | long | Hresult. |
| hresult_errorcode | long | Hresult errorcode. |
| id | long | identifier. |
| in_flight_invalidated_due_to_reclaim_count | long | Number of in flight invalidated due to reclaim. |
| init_adjust_read_carry_high | long | Init adjust read carry high. |
| init_adjust_read_carry_low | long | Init adjust read carry low. |
| init_adjust_read_concurrent_failure | long | Init adjust read concurrent failure. |
| init_adjust_read_empty_read_range | long | Init adjust read empty read range. |
| init_adjust_read_first_view_is_read | long | Init adjust read first view is read. |
| init_adjust_read_first_view_is_write | long | Init adjust read first view is write. |
| init_adjust_read_merge_high | long | Init adjust read merge high. |
| init_adjust_read_merge_low | long | Init adjust read merge low. |
| init_adjust_read_trim_read_range | long | Init adjust read trim read range. |
| init_adjust_read_wraparound_read | long | Init adjust read wraparound read. |
| init_adjust_read_wraparound_write | long | Init adjust read wraparound write. |
| init_adjust_read_write_invalidate_attempt | long | Init adjust read write invalidate attempt. |
| initial_lsn | string | Initial lsn. |
| instance_id1 | long | Instance id1. |
| instance_id2 | long | Instance id2. |
| instance_partition_id | string | Instance partition identifier. |
| instance_replica_id | long | Instance replica identifier. |
| io_req_pool_max_used_count | long | Number of I/O req pool max used. |
| io_size | long | I/O size. |
| io_size_in_bytes | long | I/O size in size in bytes. |
| is_KLL | bool | Boolean flag indicating whether KLL. |
| is_asynchronous | bool | Boolean flag indicating whether asynchronous. |
| is_compute | bool | Boolean flag indicating whether compute. |
| is_forwarder | bool | Boolean flag indicating whether forwarder. |
| is_frozen | bool | Boolean flag indicating whether frozen. |
| is_gc_iteration_end | bool | Boolean flag indicating whether gc iteration end. |
| is_incremental_checkpoint | bool | Boolean flag indicating whether incremental checkpoint. |
| is_log_replica_flavor | bool | Boolean flag indicating whether log replica flavor. |
| is_physical_sync_asynchronous | bool | Boolean flag indicating whether physical sync asynchronous. |
| is_primary | bool | Boolean flag indicating whether primary. |
| is_qos | bool | Boolean flag indicating whether qos. |
| is_qos_probe | bool | Boolean flag indicating whether qos probe. |
| is_rebind_skipped | bool | Boolean flag indicating whether rebind skipped. |
| is_recovery_in_progress | bool | Boolean flag indicating whether recovery in progress. |
| is_recovery_skipped | bool | Boolean flag indicating whether recovery skipped. |
| is_shutdown_event | bool | Boolean flag indicating whether shutdown event. |
| is_system_task | bool | Boolean flag indicating whether system task. |
| is_vlf | bool | Boolean flag indicating whether vlf. |
| iterator_create_retry_count | long | Number of iterator create retry. |
| kb_behind_min_lsn | long | Kb behind min lsn. |
| lag_or_timeout_threshold | long | Lag or timeout threshold. |
| last_bsn | long | Last bsn. |
| last_bucket_time | datetime | Last bucket time timestamp. |
| last_destage_block_bsn | long | Last destage block bsn. |
| last_destaged_bsn_timestamp | string | Last destaged bsn timestamp. |
| last_long_io_offset | long | Last long I/O offset. |
| last_received_lsn | string | Last received lsn. |
| last_redone_lsn | string | Last redone lsn. |
| last_user_trans_committed_lsn | string | Last user trans committed lsn. |
| last_user_trans_committed_time | string | Last user trans committed time timestamp. |
| last_valid_block | long | Last valid block. |
| last_valid_page | long | Last valid page. |
| latency_bucket_us | long | Latency bucket us. |
| latency_hits_00 | long | Latency hits 00. |
| latency_hits_01 | long | Latency hits 01. |
| latency_hits_02 | long | Latency hits 02. |
| latency_hits_03 | long | Latency hits 03. |
| latency_hits_04 | long | Latency hits 04. |
| latency_hits_05 | long | Latency hits 05. |
| latency_hits_06 | long | Latency hits 06. |
| latency_hits_07 | long | Latency hits 07. |
| latency_hits_08 | long | Latency hits 08. |
| latency_hits_09 | long | Latency hits 09. |
| latency_hits_10 | long | Latency hits 10. |
| latency_hits_11 | long | Latency hits 11. |
| latency_hits_12 | long | Latency hits 12. |
| latency_hits_13 | long | Latency hits 13. |
| latency_hits_14 | long | Latency hits 14. |
| latency_hits_15 | long | Latency hits 15. |
| latency_hits_total | long | Latency hits total. |
| latency_map_type | string | Type classification for latency map. |
| latency_source | string | Latency source. |
| line | long | Line. |
| linear_bsn | long | Linear bsn. |
| local_endpoint | string | Local endpoint. |
| local_file_size | long | Local file size. |
| local_state_bsn | long | Local state bsn. |
| local_state_lsn | string | Local state lsn. |
| lock_acquire_time_us | long | Lock acquire time us. |
| lockspace_nest_id | long | Lockspace nest identifier. |
| lockspace_sub_id | long | Lockspace sub identifier. |
| lockspace_workspace_id | string | Lockspace workspace identifier. |
| log_block_id | long | Log block identifier. |
| log_bytes_accepted | long | Log size in bytes accepted. |
| log_bytes_balance | long | Log size in bytes balance. |
| log_bytes_consumed | long | Log size in bytes consumed. |
| log_bytes_flushed | long | Log size in bytes flushed. |
| log_bytes_generated | long | Log size in bytes generated. |
| log_bytes_non_xact | long | Log size in bytes non xact. |
| log_bytes_non_xact_critical | long | Log size in bytes non xact critical. |
| log_bytes_non_xact_critical_governed | long | Log size in bytes non xact critical governed. |
| log_bytes_non_xact_governed | long | Log size in bytes non xact governed. |
| log_bytes_overhead | long | Log size in bytes overhead. |
| log_bytes_redo_time_ms | long | Log size in bytes redo time ms in milliseconds. |
| log_bytes_redone | long | Log size in bytes redone. |
| log_context | long | Log context. |
| log_current_limit | long | Log current limit. |
| log_current_wait_type | long | Type classification for log current wait. |
| log_flush_max_wait_time_ms | long | Log flush max wait time ms in milliseconds. |
| log_flush_wait_time_ms | long | Log flush wait time ms in milliseconds. |
| log_flush_waits | long | Log flush waits. |
| log_generation_max_stall_time_ms | long | Log generation max stall time ms in milliseconds. |
| log_generation_stall_time_ms | long | Log generation stall time ms in milliseconds. |
| log_generation_stalls | long | Log generation stalls. |
| log_kbytes_consumed | long | Log kbytes consumed. |
| log_movement_signaled | long | Log movement signaled. |
| log_op | string | Log op. |
| log_op_code | long | Log op code. |
| log_op_details | long | Log op details. |
| log_pool_miss_count | long | Number of log pool miss. |
| log_rate_bps | long | Log rate bps. |
| log_rec_hash | long | Log rec hash. |
| log_rec_lsn | string | Log rec lsn. |
| log_record_count | long | Number of log record. |
| log_record_lsn | string | Log record lsn. |
| log_record_time | long | Log record time timestamp. |
| log_replay_active_time_in_microsec | long | Log replay active time in microsec. |
| log_replay_read_time_in_microsec | long | Log replay read time in microsec. |
| log_replay_stall_time_in_microsec | long | Log replay stall time in microsec. |
| log_rg_wait_time_ms | long | Log resource governor wait time ms in milliseconds. |
| log_rg_waits | long | Log resource governor waits. |
| log_scan_function | string | Log scan function. |
| log_wait_for_flush_maximum_time | long | Log wait for flush maximum time timestamp. |
| log_wait_for_flush_time | long | Log wait for flush time timestamp. |
| log_wait_for_flush_time_count | long | Number of log wait for flush time. |
| log_writes_completed | long | Log writes completed. |
| log_writes_issued | long | Log writes issued. |
| logical_database_guid | string | Logical database guid. |
| logical_database_id | string | Logical database identifier. |
| logical_database_name | string | Logical database name. |
| logical_db_id | string | Logical database identifier. |
| logical_db_name | string | Logical database name. |
| logical_growth_id | long | Logical growth identifier. |
| logical_write_offset | long | Logical write offset. |
| logpool_total_read_count | long | Number of logpool total read. |
| longer_than_sec | long | Longer than sec. |
| lsn | string | Lsn. |
| lt_last_block | long | Lt last block. |
| lt_stg_blob_name_prefix | string | Lt stg blob name prefix. |
| lt_stg_container | string | Lt stg container. |
| lz_first_vlf | long | Lz first vlf. |
| lz_flush_bsn | long | Lz flush bsn. |
| lz_last_block | long | Lz last block. |
| lz_last_vlf | long | Lz last vlf. |
| lz_path | string | Lz path. |
| lz_tos_iter_invalidated | long | Lz tos iter invalidated. |
| lz_valid_vlfs | long | Lz valid vlfs. |
| lz_write_offset | long | Lz write offset. |
| map_count | long | Number of map. |
| marked_as_reclaim_leftover_count | long | Number of marked as reclaim leftover. |
| marked_for_reclaim_count | long | Number of marked for reclaim. |
| max | long | Max. |
| max_depth | long | Maximum depth. |
| max_distance | long | Maximum distance. |
| max_fix_time_page_id | long | Max fix time page identifier. |
| max_flush_bsn | long | Maximum flush bsn. |
| max_log_rate | long | Maximum log rate. |
| max_lsn | string | Maximum lsn. |
| max_page_fix_time_us | long | Maximum page fix time us. |
| max_page_lsn | string | Maximum page lsn. |
| max_processing_time_ms | long | Maximum processing time ms. |
| max_qos_send_interval | long | Maximum qos send interval. |
| max_redo_page_id | long | Max redo page identifier. |
| max_request_service_time | long | Max request service time timestamp. |
| max_score_of_hotpage_from_connection | real | Maximum score of hotpage from connection. |
| max_score_of_hotpage_in_rbpex | real | Maximum score of hotpage in rbpex. |
| max_size | long | Maximum size. |
| max_time_spent_in_queue | long | Maximum time spent in queue. |
| max_time_us | long | Maximum time us. |
| max_validatable_bit | long | Maximum validatable bit. |
| max_validatable_bit_crossed | bool | Boolean flag indicating whether max validatable bit crossed. |
| message | string | Human-readable message text. |
| message_systemmetadata | string | Message systemmetadata. |
| metadata_state | string | State value for metadata. |
| migrate_from_lz_dup | long | Migrate from lz dup. |
| migrate_from_stage | long | Migrate from stage. |
| migrate_from_stage_dup | long | Migrate from stage dup. |
| min | long | Min. |
| min_distance | long | Minimum distance. |
| min_lsn | string | Minimum lsn. |
| min_qos_send_interval | long | Minimum qos send interval. |
| min_score_of_hotpage_from_connection | real | Minimum score of hotpage from connection. |
| min_score_of_hotpage_in_rbpex | real | Minimum score of hotpage in rbpex. |
| min_time_us | long | Minimum time us. |
| minimum_lsn | string | Minimum lsn. |
| mismatched_offset_delete_count | long | Number of mismatched offset delete. |
| mismatched_offset_reclaim_count | long | Number of mismatched offset reclaim. |
| mode | string | Mode. |
| modified_io_bytes | long | Modified I/O size in bytes. |
| modified_io_in_pages | long | Modified I/O in pages. |
| modified_pages_lower_bits | long | Modified pages lower bits. |
| modified_pages_upper_bits | long | Modified pages upper bits. |
| modified_pages_zero_count | long | Number of modified pages zero. |
| new_file_size | long | New file size. |
| new_size | long | New size. |
| new_vlf | long | New vlf. |
| newest_lsn | string | Newest lsn. |
| next_block | long | Next block. |
| next_bsn | long | Next bsn. |
| next_expected_bsn | long | Next expected bsn. |
| next_lsn | string | Next lsn. |
| next_pair_prisnap_name | string | Next pair prisnap name. |
| next_pair_secsnap_name | string | Next pair secsnap name. |
| next_pair_state | long | State value for next pair. |
| next_pair_state_desc | string | Next pair state desc. |
| no_page_stream_stalled | long | No page stream stalled. |
| node_id | long | Node identifier. |
| num_entries | long | Num entries. |
| num_finished_work_items | long | Num finished work items. |
| num_retries_locator_release | long | Num retries locator release. |
| num_txns_to_process | long | Num txns to process. |
| num_work_items | long | Num work items. |
| num_zones_logically_reclaimed | long | Num zones logically reclaimed. |
| num_zones_physically_reclaimed | long | Num zones physically reclaimed. |
| num_zones_to_reclaim | long | Num zones to reclaim. |
| object_id | long | Object identifier. |
| occurrences | long | Occurrences. |
| old_size | long | Old size. |
| oldestXactBsn | long | Oldest Xact Bsn. |
| oldest_bsn | long | Oldest bsn. |
| oldest_lsn | string | Oldest lsn. |
| oldest_lsn_str | string | Oldest lsn str. |
| open_db_wait_in_microsec | long | Open database wait in microsec. |
| openblob_count | long | Number of openblob. |
| openblob_max_time_ms | long | Openblob max time ms in milliseconds. |
| openblob_total_time_ms | long | Openblob total time ms in milliseconds. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| original_foreign_redo_lsn | string | Original foreign redo lsn. |
| out_of_disk | bool | Boolean flag indicating whether out of disk. |
| outcome | string | Outcome. |
| own_prop_len_bytes | long | Own prop len size in bytes. |
| own_prop_name | string | Own prop name. |
| own_set_bits_after | long | Own set bits after. |
| owned_pages | long | Owned pages. |
| owner_type | string | Type classification for owner. |
| package | string | Package. |
| page_allocation_unit_id | long | Page allocation unit identifier. |
| page_count | long | Number of page. |
| page_count_0 | long | Page count 0. |
| page_count_1 | long | Page count 1. |
| page_count_2 | long | Page count 2. |
| page_count_3 | long | Page count 3. |
| page_count_4 | long | Page count 4. |
| page_count_5 | long | Page count 5. |
| page_count_6 | long | Page count 6. |
| page_count_7 | long | Page count 7. |
| page_count_8 | long | Page count 8. |
| page_count_more_than_8 | long | Page count more than 8. |
| page_db_name | string | Page database name. |
| page_filter | long | Page filter. |
| page_fix_total_us | long | Page fix total us. |
| page_id | long | Page identifier. |
| page_index | long | Page index. |
| page_io_wait_in_microsec | long | Page I/O wait in microsec. |
| page_lsn | string | Page lsn. |
| page_modified_found | long | Page modified found. |
| page_operation_incomplete | long | Page operation incomplete. |
| page_server_checkpoint_lsn | string | Page server checkpoint lsn. |
| page_server_client_role | string | Page server client role. |
| page_split_due_to_sys_tran | long | Page split due to sys tran. |
| page_type | long | Type classification for page. |
| pages_deleted_count | long | Number of pages deleted. |
| pages_found_count | long | Number of pages found. |
| pages_kb | long | Pages kb. |
| pages_modified_segment_end_found | long | Pages modified segment end found. |
| pages_on_evicted_segment_skipped_count | long | Number of pages on evicted segment skipped. |
| pages_on_uncovered_segment_skipped_count | long | Number of pages on uncovered segment skipped. |
| pages_on_zeroed_out_segment_skipped_count | long | Number of pages on zeroed out segment skipped. |
| pages_returned | long | Pages returned. |
| pages_skipped_count | long | Number of pages skipped. |
| pages_stats | string | Pages stats. |
| pages_trimmed_on_the_left_count | long | Number of pages trimmed on the left. |
| pages_trimmed_on_the_right_count | long | Number of pages trimmed on the right. |
| pages_unlinked | long | Pages unlinked. |
| pages_unlinked_0 | long | Pages unlinked 0. |
| pages_unlinked_gt_1000 | long | Pages unlinked gt 1000. |
| pages_unlinked_le_10 | long | Pages unlinked le 10. |
| pages_unlinked_le_100 | long | Pages unlinked le 100. |
| pages_unlinked_le_1000 | long | Pages unlinked le 1000. |
| pages_unlinked_le_2 | long | Pages unlinked le 2. |
| pages_unlinked_le_5 | long | Pages unlinked le 5. |
| pages_unlinked_le_50 | long | Pages unlinked le 50. |
| pages_validated | long | Pages validated. |
| pageserver_endpoint | string | Pageserver endpoint. |
| parent_page_with_pending_lsns | long | Parent page with pending lsns. |
| parse_io_count_invocation | long | Parse I/O count invocation. |
| parse_io_total_time | long | Parse I/O total time timestamp. |
| partition_id | string | Partition identifier. |
| peer_prop_len_bytes | long | Peer prop len size in bytes. |
| peer_prop_name | string | Peer prop name. |
| peer_replica | bool | Boolean flag indicating whether peer replica. |
| peer_set_bits_after | long | Peer set bits after. |
| pend_io_count_invocation | long | Pend I/O count invocation. |
| pend_io_total_time | long | Pend I/O total time timestamp. |
| percent_complete | long | Percent complete. |
| percent_seeded | long | Percent seeded. |
| percentile_0 | long | Percentile 0. |
| percentile_25 | long | Percentile 25. |
| percentile_50 | long | Percentile 50. |
| percentile_75 | long | Percentile 75. |
| percentile_90 | long | Percentile 90. |
| percentile_95 | long | Percentile 95. |
| percentile_99 | long | Percentile 99. |
| percentile_999 | long | Percentile 999. |
| performance_counter_type | string | Type classification for performance counter. |
| period_ms | long | Period ms in milliseconds. |
| persisted_bitmap_length_bytes | long | Persisted bitmap length size in bytes. |
| persisted_foreign_redo_lsn | string | Persisted foreign redo lsn. |
| persisted_own_set_bits_before | long | Persisted own set bits before. |
| persisted_peer_set_bits_before | long | Persisted peer set bits before. |
| phase | string | Phase. |
| physical_database_guid | string | Physical database guid. |
| physical_database_id | string | Physical database identifier. |
| physical_database_name | string | Physical database name. |
| physical_db_id | string | Physical database identifier. |
| physical_db_name | string | Physical database name. |
| physical_file_size_kb | long | Physical file size kb. |
| pool_trunc_lsn | string | Pool trunc lsn. |
| post_free_page_locator_count | long | Number of post free page locator. |
| post_free_segment_locator_count | long | Number of post free segment locator. |
| post_wk_delete_queue_count | long | Number of post wk delete queue. |
| post_wk_error_count | long | Number of post wk error. |
| post_wk_ex_retries_queue_count | long | Number of post wk ex retries queue. |
| pre_free_page_locator_count | long | Number of pre free page locator. |
| pre_free_segment_locator_count | long | Number of pre free segment locator. |
| prev_event | string | Prev event. |
| prev_page_lsn | string | Prev page lsn. |
| previous_file_size | long | Previous file size. |
| previous_full | long | Previous full. |
| previous_size | long | Previous size. |
| priming_id | long | Priming identifier. |
| process_id | long | Process identifier. |
| property_name | string | Property name. |
| query_hash | long | Query hash. |
| quota_diff_mb | long | Quota diff mb. |
| ratelimiter_read_enqueued | long | Ratelimiter read enqueued. |
| ratelimiter_read_issued | long | Ratelimiter read issued. |
| ratelimiter_self_throttled | long | Ratelimiter self throttled. |
| ratelimiter_write_enqueued | long | Ratelimiter write enqueued. |
| ratelimiter_write_issued | long | Ratelimiter write issued. |
| rbio_attempt_num | long | Rbio attempt num. |
| rbio_msg_type | string | Type classification for rbio msg. |
| rbio_send_response_time_in_microsec | long | Rbio send response time in microsec. |
| rbpex_new_size | long | Rbpex new size. |
| rbpex_previous_size | long | Rbpex previous size. |
| rbpex_size_on_disk_mb | long | Rbpex size on disk mb. |
| read_ahead_map_hit | long | Read ahead map hit. |
| read_ahead_map_miss | long | Read ahead map miss. |
| read_ahead_time_in_microsec | long | Read ahead time in microsec. |
| read_as_fcb_broker_backward_search | long | Read as fcb broker backward search. |
| read_as_fcb_tos_backward_search | long | Read as fcb tos backward search. |
| read_broker_filtered_bytes | long | Read broker filtered size in bytes. |
| read_broker_hit | long | Read broker hit. |
| read_broker_miss_not_found | long | Read broker miss not found. |
| read_broker_miss_timeout | long | Read broker miss timeout. |
| read_buffer_full | long | Read buffer full. |
| read_error_completed_out_of_view | long | Read error completed out of view. |
| read_error_device | long | Read error device. |
| read_error_incomplete | long | Read error incomplete. |
| read_error_initiated_after_view | long | Read error initiated after view. |
| read_error_initiated_before_view | long | Read error initiated before view. |
| read_error_initiated_file_not_found | long | Read error initiated file not found. |
| read_error_initiated_truncated | long | Read error initiated truncated. |
| read_failed | long | Read failed. |
| read_first_access | datetime | Read first access. |
| read_from | long | Read from. |
| read_gap_filler_block_exists | long | Read gap filler block exists. |
| read_io | long | Read I/O. |
| read_last_access | datetime | Read last access. |
| read_lc_hit | long | Read lc hit. |
| read_lc_miss | long | Read lc miss. |
| read_log_bytes_returned | long | Read log size in bytes returned. |
| read_log_filtered_blocks | long | Read log filtered blocks. |
| read_lt_hit | long | Read lt hit. |
| read_lt_miss | long | Read lt miss. |
| read_lz_hit | long | Read lz hit. |
| read_lz_miss | long | Read lz miss. |
| read_not_found | long | Read not found. |
| read_not_found_retry | long | Read not found retry. |
| read_offset | long | Read offset. |
| read_only | bool | Boolean flag indicating whether read only. |
| read_single_io | long | Read single I/O. |
| read_size | long | Read size. |
| read_split_io | long | Read split I/O. |
| read_successful | long | Read successful. |
| read_successful_child | long | Read successful child. |
| read_tiered_log_record_filtered_bytes_copied | long | Read tiered log record filtered size in bytes copied. |
| read_tiered_log_record_filtered_bytes_read | long | Read tiered log record filtered size in bytes read. |
| read_tiered_log_record_filtered_read_count | long | Number of read tiered log record filtered read. |
| read_tiered_log_record_opaque_bytes_copied | long | Read tiered log record opaque size in bytes copied. |
| read_tiered_log_record_opaque_bytes_read | long | Read tiered log record opaque size in bytes read. |
| read_tiered_log_record_opaque_read_count | long | Number of read tiered log record opaque read. |
| read_vlf_from_broker | long | Read vlf from broker. |
| read_vlf_from_lc | long | Read vlf from lc. |
| read_vlf_from_lt | long | Read vlf from lt. |
| read_vlf_from_lz | long | Read vlf from lz. |
| readcount | long | Readcount. |
| reads_from_broker | long | Reads from broker. |
| reads_from_lc | long | Reads from lc. |
| reads_from_lt | long | Reads from lt. |
| reads_from_lz | long | Reads from lz. |
| reads_from_pool | long | Reads from pool. |
| rebalance_reason | string | Rebalance reason. |
| rebase_iteration | long | Rebase iteration. |
| rebind_reasons | long | Rebind reasons. |
| rebind_stream_count | long | Number of rebind stream. |
| reclaim_page_update_row_failed_count | long | Number of reclaim page update row failed. |
| recovery_elapsed_time_ms | long | Recovery elapsed time ms in milliseconds. |
| recovery_phase | string | Recovery phase. |
| recovery_stage | string | Recovery stage. |
| recovery_step | string | Recovery step. |
| recovery_time | long | Recovery time timestamp. |
| redirection_endpoint | long | Redirection endpoint. |
| redirection_state_v2 | string | Redirection state v2. |
| redo_active_time_count | long | Number of redo active time. |
| redo_call_stack | string | Redo call stack. |
| redo_maximum_active_time | long | Redo maximum active time timestamp. |
| redo_maximum_read_time | long | Redo maximum read time timestamp. |
| redo_maximum_stall_time | long | Redo maximum stall time timestamp. |
| redo_queue_bytes | long | Redo queue size in bytes. |
| redo_read_time_count | long | Number of redo read time. |
| redo_stall_time_count | long | Number of redo stall time. |
| redo_thread_active_time | long | Redo thread active time timestamp. |
| redo_thread_read_time | long | Redo thread read time timestamp. |
| redo_thread_stall_time | long | Redo thread stall time timestamp. |
| redolsn | string | Redolsn. |
| redone_count | long | Number of redone. |
| redone_total_us | long | Redone total us. |
| referenceBsn | long | Reference Bsn. |
| released_pages | long | Released pages. |
| remap_page_id_count | long | Number of remap page id. |
| remap_page_id_time | long | Remap page id time timestamp. |
| remote_ckpt_bsn | long | Remote ckpt bsn. |
| remote_endpoint | string | Remote endpoint. |
| remote_endpoint_from | string | Remote endpoint from. |
| remote_endpoint_to | string | Remote endpoint to. |
| remote_file_size | long | Remote file size. |
| remote_from_resolved_0 | string | Remote from resolved 0. |
| remote_from_resolved_1 | string | Remote from resolved 1. |
| remote_state_bsn | long | Remote state bsn. |
| remote_state_lsn | string | Remote state lsn. |
| remote_to_resolved_0 | string | Remote to resolved 0. |
| remote_to_resolved_1 | string | Remote to resolved 1. |
| replica_rebuild_evaluation_time | long | Replica rebuild evaluation time timestamp. |
| replication_lag_in_secs | long | Replication lag in secs. |
| reported_permanent_fault | bool | Boolean flag indicating whether reported permanent fault. |
| req_id | long | Req identifier. |
| req_type | string | Type classification for req. |
| request_for_eol | bool | Boolean flag indicating whether request for eol. |
| request_list_empty | long | Request list empty. |
| request_list_full | long | Request list full. |
| request_service_time_count | long | Number of request service time. |
| request_timeout_signaled | long | Request timeout signaled. |
| requested_page_type | string | Type classification for requested page. |
| requests_serviced_log_move | long | Requests serviced log move. |
| requests_serviced_timeout | long | Requests serviced timeout. |
| resend_count | long | Number of resend. |
| reserved_pages | long | Reserved pages. |
| reset_scan_complete_count | long | Number of reset scan complete. |
| reset_scan_complete_max_time | long | Reset scan complete max time timestamp. |
| reset_scan_complete_total_time | long | Reset scan complete total time timestamp. |
| reset_state | long | State value for reset. |
| resolved_address | string | Resolved address. |
| resource_0 | long | Resource 0. |
| resource_1 | long | Resource 1. |
| resource_2 | long | Resource 2. |
| resource_description | string | Resource description. |
| resource_type | string | Type classification for resource. |
| result | long | Result. |
| retrieve_block_count_invocation | long | Retrieve block count invocation. |
| retrieve_block_total_time | long | Retrieve block total time timestamp. |
| retry_failed | long | Retry failed. |
| returned_from | string | Returned from. |
| returned_from_eol_pool | long | Returned from eol pool. |
| roundtrip_time_us_from | long | Roundtrip time us from. |
| roundtrip_time_us_to | long | Roundtrip time us to. |
| sample_phase_runtime_ms | long | Sample phase runtime ms in milliseconds. |
| sample_phase_runtime_us | long | Sample phase runtime us. |
| sampling_strategy | string | Sampling strategy. |
| scan_start_bsn | long | Scan start bsn. |
| scanned_blocks | long | Scanned blocks. |
| scheduler_address | string | Scheduler address. |
| second_begin_lsn | string | Second begin lsn. |
| second_file_name | string | Second file name. |
| second_name | string | Second name. |
| seconds_since_reset | long | Seconds since reset. |
| sector_id | long | Sector identifier. |
| segment_beyond_local_file_size | long | Segment beyond local file size. |
| segment_exhausted | long | Segment exhausted. |
| segment_id | long | Segment identifier. |
| segment_occupancy_bucket_00 | long | Segment occupancy bucket 00. |
| segment_occupancy_bucket_01 | long | Segment occupancy bucket 01. |
| segment_occupancy_bucket_02 | long | Segment occupancy bucket 02. |
| segment_occupancy_bucket_03 | long | Segment occupancy bucket 03. |
| segment_occupancy_bucket_04 | long | Segment occupancy bucket 04. |
| segment_occupancy_bucket_05 | long | Segment occupancy bucket 05. |
| segment_occupancy_bucket_06 | long | Segment occupancy bucket 06. |
| segment_occupancy_bucket_07 | long | Segment occupancy bucket 07. |
| segment_occupancy_bucket_max | long | Segment occupancy bucket max. |
| segment_size_kb | long | Segment size kb. |
| sessionName | string | Session Name. |
| set_bits | long | Set bits. |
| severity | long | Severity level associated with the event. |
| shared_pool_size | long | Shared pool size. |
| shrink_cancelled | long | Shrink cancelled. |
| shrink_cancelled_due_rbpex_draining | long | Shrink cancelled due rbpex draining. |
| shrink_id | long | Shrink identifier. |
| simulated | long | Simulated. |
| size_in_kb | long | Size in kb. |
| size_to_grow_mb | long | Size to grow mb. |
| size_to_grow_rounded_to_zones_mb | long | Size to grow rounded to zones mb. |
| skip_size_init | bool | Boolean flag indicating whether skip size init. |
| sleep_duration_bucket_00 | long | Sleep duration bucket 00. |
| sleep_duration_bucket_01 | long | Sleep duration bucket 01. |
| sleep_duration_bucket_02 | long | Sleep duration bucket 02. |
| sleep_duration_bucket_03 | long | Sleep duration bucket 03. |
| sleep_duration_bucket_04 | long | Sleep duration bucket 04. |
| sleep_duration_bucket_05 | long | Sleep duration bucket 05. |
| sleep_duration_bucket_06 | long | Sleep duration bucket 06. |
| slog_redone_count | long | Number of slog redone. |
| slog_redone_total_us | long | Slog redone total us. |
| snapshot_duration_ms | long | Snapshot duration ms in milliseconds. |
| snapshot_name | string | Snapshot name. |
| snapshot_pair | string | Snapshot pair. |
| soft_retry_count_endpoint_0 | long | Soft retry count endpoint 0. |
| soft_retry_count_endpoint_1 | long | Soft retry count endpoint 1. |
| sos_result | long | Sos result. |
| source_worker | string | Source worker. |
| sourceindex | long | Sourceindex. |
| sparse_size_mb | long | Sparse size mb. |
| sql_error | long | SQL error. |
| staged_block_allocated | long | Staged block allocated. |
| staged_block_payload_allocated | long | Staged block payload allocated. |
| staged_block_payload_reused | long | Staged block payload reused. |
| staged_block_reused | long | Staged block reused. |
| staged_blocks | long | Staged blocks. |
| staged_bytes | long | Staged size in bytes. |
| start_block | long | Start block. |
| start_bsn_id | long | Start bsn identifier. |
| start_offset | long | Start offset. |
| start_page_id | long | Start page identifier. |
| starting_bit | long | Starting bit. |
| starting_pageids | string | Starting pageids. |
| state | long | Current lifecycle or health state. |
| state_desc | string | State desc. |
| stop_at | string | Stop at. |
| store_name | string | Store name. |
| stream_exhausted | long | Stream exhausted. |
| stream_id | string | Stream identifier. |
| striped_end_page | long | Striped end page. |
| striped_start_page | long | Striped start page. |
| success_conn_count_endpoint_0 | long | Success conn count endpoint 0. |
| success_conn_count_endpoint_1 | long | Success conn count endpoint 1. |
| success_grow_zones | long | Success grow zones. |
| successful_commit | long | Successful commit. |
| successful_lazy_commit | long | Successful lazy commit. |
| sys_requests_recvd | long | Sys requests recvd. |
| sys_requests_sent | long | Sys requests sent. |
| sys_responses_recvd | long | Sys responses recvd. |
| sys_responses_sent | long | Sys responses sent. |
| sys_retry_after_back_off | long | Sys retry after back off. |
| sys_time_spent_on_qos_us | long | Sys time spent on qos us. |
| system_thread_id | long | System thread identifier. |
| tail_log_cache_miss_count | long | Number of tail log cache miss. |
| target_checkpoint_lsn | string | Target checkpoint lsn. |
| target_lsn | string | Target lsn. |
| target_worker | string | Target worker. |
| task_aborted_process_shrink | long | Task aborted process shrink. |
| task_name | string | Task name. |
| thread_switch_count | long | Number of thread switch. |
| threshold_triggered | bool | Boolean flag indicating whether threshold triggered. |
| throttle_potential_reason | string | Throttle potential reason. |
| throttle_reason | string | Throttle reason. |
| throttling_source | string | Throttling source. |
| ticks | long | Ticks. |
| time_release_remaining_page_locators_in_ms | long | Time release remaining page locators in ms in milliseconds. |
| time_shrink_cleanup_in_ms | long | Time shrink cleanup in ms in milliseconds. |
| time_shrink_delete_or_retry_in_ms | long | Time shrink delete or retry in ms in milliseconds. |
| time_shrink_delete_txn_commit_in_ms | long | Time shrink delete txn commit in ms in milliseconds. |
| time_shrink_physical_async_in_ms | long | Time shrink physical async in ms in milliseconds. |
| time_shrink_physical_call_latency_in_ms | long | Time shrink physical call latency in ms in milliseconds. |
| time_shrink_reclaim_in_ms | long | Time shrink reclaim in ms in milliseconds. |
| time_spent_before_resend_ms | long | Time spent before resend ms in milliseconds. |
| time_spent_in_queue_count | long | Number of time spent in queue. |
| time_taken_in_sec | long | Time taken in sec. |
| time_taken_millisec | long | Time taken millisec. |
| time_to_migrate | long | Time to migrate. |
| time_to_update | long | Time to update. |
| time_waiting_for_gc_in_ms | long | Time waiting for gc in ms in milliseconds. |
| timeout | long | Timeout. |
| timeout_ms | long | Timeout ms in milliseconds. |
| timer_elapsed_time_in_sec | long | Timer elapsed time in sec. |
| timer_expired | long | Timer expired. |
| timer_interval_in_sec | long | Timer interval in sec. |
| timestamp_scheduler_ring_buffer_recorded | long | Timestamp scheduler ring buffer recorded. |
| to_size_in_pages | long | To size in pages. |
| tos_file_tier | string | Tos file tier. |
| tos_iter_tier | string | Tos iter tier. |
| tos_lc_first_bsn | long | Tos lc first bsn. |
| tos_lc_last_bsn | long | Tos lc last bsn. |
| tos_lc_miss | long | Tos lc miss. |
| tos_lc_vlf_count | long | Number of tos lc vlf. |
| tos_lc_vlf_size_in_mb | long | Tos lc vlf size in mb. |
| tos_lt_first_bsn | long | Tos lt first bsn. |
| tos_lt_last_bsn | long | Tos lt last bsn. |
| tos_lt_vlf_count | long | Number of tos lt vlf. |
| tos_lt_vlf_size_in_mb | long | Tos lt vlf size in mb. |
| tos_lz_first_bsn | long | Tos lz first bsn. |
| tos_lz_last_bsn | long | Tos lz last bsn. |
| tos_lz_vlf_count | long | Number of tos lz vlf. |
| tos_lz_vlf_size_in_mb | long | Tos lz vlf size in mb. |
| total_bytes_grown | long | Total size in bytes grown. |
| total_cancelled_failed_io_count | long | Number of total cancelled failed I/O. |
| total_cancelled_retry_io_count | long | Number of total cancelled retry I/O. |
| total_cancelled_write_io_count | long | Number of total cancelled write I/O. |
| total_count | long | Number of total. |
| total_elapsed_time_sec | long | Total elapsed time sec. |
| total_gap_filled_blocks | long | Total gap filled blocks. |
| total_grown_latency | long | Total grown latency. |
| total_io_bytes | long | Total I/O size in bytes. |
| total_io_in_pages | long | Total I/O in pages. |
| total_iterators_count | long | Number of total iterators. |
| total_locked_bytes | long | Total locked size in bytes. |
| total_locked_in_pages | long | Total locked in pages. |
| total_migrated_blocks | long | Total migrated blocks. |
| total_pages | long | Total pages. |
| total_pages_evicted | long | Total pages evicted. |
| total_pages_in_rbpex | long | Total pages in rbpex. |
| total_pages_scanned_for_eviction | long | Total pages scanned for eviction. |
| total_read_count | long | Number of total read. |
| total_read_io_count | long | Number of total read I/O. |
| total_request_service_time | long | Total request service time timestamp. |
| total_requests | long | Total requests. |
| total_retries | long | Total retries. |
| total_segments | long | Total segments. |
| total_segments_subpar | long | Total segments subpar. |
| total_segments_subpar_evicted | long | Total segments subpar evicted. |
| total_send_count | long | Number of total send. |
| total_stalled_requests | long | Total stalled requests. |
| total_time_spent_in_queue | long | Total time spent in queue. |
| total_write_io_count | long | Number of total write I/O. |
| total_zones | long | Total zones. |
| tracked_count | long | Number of tracked. |
| tracked_iterators_count | long | Number of tracked iterators. |
| transaction_id | long | Transaction identifier. |
| tx_delete_failed_count | long | Number of tx delete failed. |
| tx_delete_row_not_found_count | long | Number of tx delete row not found. |
| tx_delete_successful_count | long | Number of tx delete successful. |
| tx_delete_waiton_lru_write_completion | long | Tx delete waiton lru write completion. |
| tx_delete_waiton_write_completion | long | Tx delete waiton write completion. |
| tx_delete_wrong_state_found | long | Tx delete wrong state found. |
| tx_ex_retries_failed_count | long | Number of tx ex retries failed. |
| tx_ex_retries_successful_count | long | Number of tx ex retries successful. |
| tx_reclaim_failed_count | long | Number of tx reclaim failed. |
| tx_reclaim_row_not_found_count | long | Number of tx reclaim row not found. |
| tx_reclaim_successful_count | long | Number of tx reclaim successful. |
| type | string | Type. |
| unavailable_zones_count | long | Number of unavailable zones. |
| uncertain_pages_skipped | long | Uncertain pages skipped. |
| unknown_io_error_count | long | Number of unknown I/O error. |
| unlink_calls | long | Unlink calls. |
| untracked_iterators_count | long | Number of untracked iterators. |
| user_remote_page_reads | long | User remote page reads. |
| user_remote_requests | long | User remote requests. |
| version | string | Version. |
| vlf_count | long | Number of vlf. |
| vlf_header_bsn | long | Vlf header bsn. |
| vlf_id | long | Vlf identifier. |
| vlf_size_in_mb | long | Vlf size in mb. |
| vlf_size_mb | long | Vlf size mb. |
| vm_committed_kb | long | Vm committed kb. |
| wait_count | long | Number of wait. |
| wait_for_broker_full_timeout_ms | long | Wait for broker full timeout ms in milliseconds. |
| wait_for_redo_location | string | Wait for redo location. |
| wait_for_redo_page_type | string | Type classification for wait for redo page. |
| wait_signaled_on_broker_max | long | Wait signaled on broker max. |
| wait_signaled_on_min_time_move | long | Wait signaled on min time move. |
| wait_signaled_on_min_wait | long | Wait signaled on min wait. |
| wait_time_ms | long | Wait time in milliseconds. |
| wait_type | string | Wait type name. |
| wb_log_dist_threshold_in_kb | long | Wb log dist threshold in kb. |
| wk_delete_queue_count | long | Number of wk delete queue. |
| wk_ex_retries_queue_count | long | Number of wk ex retries queue. |
| worker_signal_time | long | Worker signal time timestamp. |
| write_error_device | long | Write error device. |
| write_error_incomplete | long | Write error incomplete. |
| write_first_access | datetime | Write first access. |
| write_invalidated_due_to_reclaim_count | long | Number of write invalidated due to reclaim. |
| write_last_access | datetime | Write last access. |
| write_offset | long | Write offset. |
| write_single_io | long | Write single I/O. |
| write_size | long | Write size. |
| write_split_io | long | Write split I/O. |
| write_successful | long | Write successful. |
| write_successful_child | long | Write successful child. |
| write_to | long | Write to. |
| writecount | long | Writecount. |
| xlogpool_block_removed | long | Xlogpool block removed. |
| xlogpool_duplicate_insert | long | Xlogpool duplicate insert. |
| xlogpool_entry_memory_allocation_failure | long | Xlogpool entry memory allocation failure. |
| xlogpool_filler_block_already_exists | long | Xlogpool filler block already exists. |
| xlogpool_filler_blocks_inserted | long | Xlogpool filler blocks inserted. |
| xlogpool_filler_blocks_inserted_from_lc | long | Xlogpool filler blocks inserted from lc. |
| xlogpool_filler_blocks_inserted_from_lt | long | Xlogpool filler blocks inserted from lt. |
| xlogpool_filler_blocks_inserted_from_lz | long | Xlogpool filler blocks inserted from lz. |
| xlogpool_filler_decrypt_failed | long | Xlogpool filler decrypt failed. |
| xlogpool_filler_decrypt_success | long | Xlogpool filler decrypt success. |
| xlogpool_filler_fillline_hit_lc | long | Xlogpool filler fillline hit lc. |
| xlogpool_filler_fillline_hit_lt | long | Xlogpool filler fillline hit lt. |
| xlogpool_filler_fillline_hit_lz | long | Xlogpool filler fillline hit lz. |
| xlogpool_filler_iter_reset_lc | long | Xlogpool filler iter reset lc. |
| xlogpool_filler_iter_reset_lt | long | Xlogpool filler iter reset lt. |
| xlogpool_filler_iter_reset_lz | long | Xlogpool filler iter reset lz. |
| xlogpool_filler_rob_calls | long | Xlogpool filler rob calls. |
| xlogpool_filler_rob_io_errors | long | Xlogpool filler rob I/O errors. |
| xlogpool_filler_rob_stalls | long | Xlogpool filler rob stalls. |
| xlogpool_filtered_bytes | long | Xlogpool filtered size in bytes. |
| xlogpool_hit | long | Xlogpool hit. |
| xlogpool_miss | long | Xlogpool miss. |
| xlogpool_miss_time_ms | long | Xlogpool miss time ms in milliseconds. |
| xlogpool_miss_time_us | long | Xlogpool miss time us. |
| xlogpool_query_block_time_ms | long | Xlogpool query block time ms in milliseconds. |
| xlogpool_query_block_time_us | long | Xlogpool query block time us. |
| xlogpool_retry | long | Xlogpool retry. |
| xlogreader_active_time | long | Xlogreader active time timestamp. |
| xlogreader_create_page_server_time | long | Xlogreader create page server time timestamp. |
| xlogreader_maximum_stall_time | long | Xlogreader maximum stall time timestamp. |
| xlogreader_read_time | long | Xlogreader read time timestamp. |
| xlogreader_redo_catchup_maximum_stall_time | long | Xlogreader redo catchup maximum stall time timestamp. |
| xlogreader_redo_catchup_time | long | Xlogreader redo catchup time timestamp. |
| xlogreader_redo_catchup_time_count | long | Number of xlogreader redo catchup time. |
| xlogreader_stall_time | long | Xlogreader stall time timestamp. |
| xlogreader_stall_time_count | long | Number of xlogreader stall time. |
| xlogreader_wait_for_page_server_time | long | Xlogreader wait for page server time timestamp. |
| zeroed_pages_skipped | long | Zeroed pages skipped. |
| zone_hit_count | long | Number of zone hit. |
| zone_id | long | Zone identifier. |
| zone_read_count | long | Number of zone read. |
| zones_failed_to_grow_count | long | Number of zones failed to grow. |
| zones_grown_count | long | Number of zones grown. |

# 9. Storage

## MonContainerShare — Container Share

**Purpose**: Container Share. Used to troubleshoot storage usage, persistence, I/O characteristics, and storage-engine side effects. Referenced in MI template areas: availability, networking.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| byte_size | long | Byte size. |
| certificate_has_private_key | bool | Boolean flag indicating whether certificate has private key. |
| certificate_issuer | string | Certificate issuer. |
| certificate_subject | string | Certificate subject. |
| certificate_thumbprint | string | Certificate thumbprint. |
| certificate_valid_from | datetime | Certificate valid from. |
| certificate_valid_to | datetime | Certificate valid to. |
| client_endpoint | string | Client endpoint. |
| collect_currencollect_current_thread_id | long | Collect currencollect current thread identifier. |
| collect_current_thread_id | long | Collect current thread identifier. |
| emitting_context | string | Emitting context. |
| event | string | Event name emitted by the component. |
| exception_message | string | Exception message. |
| exception_type | string | Type classification for exception. |
| host_environment_type | string | Type classification for host environment. |
| info | string | Info. |
| inner_exception_message | string | Inner exception message. |
| inner_exception_stack_trace | string | Inner exception stack trace. |
| inner_exception_type | string | Type classification for inner exception. |
| listen_address | string | Listen address. |
| listen_port | string | Listen port. |
| log_level | string | Log level. |
| log_levelcollect_currencollect_current_thread_id | string | Log levelcollect currencollect current thread identifier. |
| message | string | Human-readable message text. |
| named_pipe_path | string | Named pipe path. |
| new_value | string | New value. |
| new_value_kind | string | New value kind. |
| operation | string | Operation. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| original_value | string | Original value. |
| original_value_kind | string | Original value kind. |
| package | string | Package. |
| process_id | long | Process identifier. |
| property_name | string | Property name. |
| registry_key_path | string | Registry key path. |
| remote_endpoint | string | Remote endpoint. |
| route | string | Route. |
| route_address_family | string | Route address family. |
| route_age | long | Route age. |
| route_immortal | long | Route immortal. |
| route_interface_addresses | string | Route interface addresses. |
| route_interface_index | long | Route interface index. |
| route_interface_luid | long | Route interface luid. |
| route_lifetime_preferred | string | Route lifetime preferred. |
| route_lifetime_valid | string | Route lifetime valid. |
| route_metric | long | Route metric. |
| route_protocol | long | Route protocol. |
| sessionName | string | Session Name. |
| session_id | string | Session identifier. |
| stack_trace | string | Stack trace. |
| startup_state | string | State value for startup. |
| state | string | Current lifecycle or health state. |
| status | string | Current status reported by the component. |
| step | string | Step. |
| store_location | string | Store location. |
| store_name | string | Store name. |
| subkey_name | string | Subkey name. |
| value | string | Value. |
| value_kind | string | Value kind. |

## MonSqlShrinkInfo — SQL Shrink Info

**Purpose**: SQL Shrink Info. Used to troubleshoot storage usage, persistence, I/O characteristics, and storage-engine side effects. Referenced in MI template areas: availability, performance.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| alloc_unit_id | long | Alloc unit identifier. |
| allocation_unit_type | string | Type classification for allocation unit. |
| btree_pages_moved | long | Btree pages moved. |
| code_package_version | string | Code package version. |
| columnstore_dictionaries_moved | long | Columnstore dictionaries moved. |
| columnstore_lob_pages_moved | long | Columnstore lob pages moved. |
| columnstore_segments_moved | long | Columnstore segments moved. |
| compressed_segment_moves_failed | long | Compressed segment moves failed. |
| compressed_segment_moves_skipped | long | Compressed segment moves skipped. |
| compressed_segments_moved | long | Compressed segments moved. |
| count_of_lobs_moved | long | Number of count of lobs moved. |
| count_of_lobs_skipped | long | Number of count of lobs skipped. |
| database_id | long | Database identifier. |
| duration_in_ms | long | Duration in ms in milliseconds. |
| event | string | Event name emitted by the component. |
| failure_reason | string | Failure reason. |
| file_id | long | File identifier. |
| file_size | string | File size. |
| heap_pages_moved | long | Heap pages moved. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| iam_pages_moved | long | Iam pages moved. |
| index_id | long | Index identifier. |
| is_column_store | bool | Boolean flag indicating whether column store. |
| lob_pages_moved | long | Lob pages moved. |
| logical_database_guid | string | Logical database guid. |
| logical_database_name | string | Logical database name. |
| move_range_end_file_id | long | Move range end file identifier. |
| move_range_end_page_id | long | Move range end page identifier. |
| move_range_start_file_id | long | Move range start file identifier. |
| move_range_start_page_id | long | Move range start page identifier. |
| object_id | long | Object identifier. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| page_id | long | Page identifier. |
| percent_complete | string | Percent complete. |
| redirect_table_rowset_id | long | Redirect table rowset identifier. |
| rowgroup_id | long | Rowgroup identifier. |
| rowset_id | long | Rowset identifier. |
| sessionName | string | Session Name. |
| shrink_id | string | Shrink identifier. |
| status | string | Current status reported by the component. |
| tag | string | Tag. |
| target_size | string | Target size. |

## MonSQLXStore — SQLXStore

**Purpose**: SQLXStore. Used to troubleshoot storage usage, persistence, I/O characteristics, and storage-engine side effects. Referenced in MI template areas: availability, backup-restore, performance. Often used during backup or restore investigations.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| Error_Message | string | Error Message. |
| Function_Module | string | Function Module. |
| IOs_failed_after_retry | long | IOs failed after retry. |
| IOs_failed_after_successful_retry | long | IOs failed after successful retry. |
| IOs_fast_failed | long | IOs fast failed. |
| IOs_queued_after_retry | long | IOs queued after retry. |
| IOs_queued_for_wait | long | IOs queued for wait. |
| IOs_retried_successfully | long | IOs retried successfully. |
| PartitionId | string | Partition Id. |
| account_dns | string | Account dns. |
| agg_volume_identity | string | Agg volume identity. |
| altered_creds_count | long | Number of altered creds. |
| alternative_endpoint | string | Alternative endpoint. |
| app_instance_id | string | App instance identifier. |
| avg_latency_threshold_ms | long | Average latency threshold ms. |
| bandwidth_limit_mibps | long | Bandwidth limit mibps. |
| bandwidth_limit_mibps_delta | long | Bandwidth limit mibps delta. |
| blob_sequence_number | long | Blob sequence number. |
| blob_size | long | Blob size. |
| blob_status | string | Status value for blob. |
| blob_tier | string | Blob tier. |
| blob_type | long | Type classification for blob. |
| burst_ios_available | long | Burst ios available. |
| burst_ios_available_delta | long | Burst ios available delta. |
| burst_ios_limit | long | Burst ios limit. |
| burst_ios_limit_delta | long | Burst ios limit delta. |
| bytes_read | long | Bytes read. |
| callback_status | long | Status value for callback. |
| cancellation_duration_usec | long | Cancellation duration usec. |
| check_previous_size_scaledown | bool | Boolean flag indicating whether check previous size scaledown. |
| close_file_handle_last_error | string | Close file handle last error. |
| close_file_handle_succeeded | bool | Boolean flag indicating whether close file handle succeeded. |
| code_package_version | string | Code package version. |
| container_name | string | Container name. |
| correlation_id | string | Correlation identifier used across components. |
| creation_disposition | long | Creation disposition. |
| credential_type | int | Type classification for credential. |
| current_premium_remote_storage_volume_type | long | Type classification for current premium remote storage volume. |
| current_seq_num | long | Current seq num. |
| database_marked_scoped_credentials_count | long | Number of database marked scoped credentials. |
| debug_trace | string | Debug trace. |
| desired_access | long | Desired access. |
| distributed_execution_id | string | Distributed execution identifier. |
| distributed_query_hash | string | Distributed query hash. |
| distributed_query_operator_id | string | Distributed query operator identifier. |
| distributed_request_id | string | Distributed request identifier. |
| distributed_scheduler_id | string | Distributed scheduler identifier. |
| distributed_statement_id | string | Distributed statement identifier. |
| distributed_step_index | string | Distributed step index. |
| distributed_submission_id | string | Distributed submission identifier. |
| distributed_task_group_id | string | Distributed task group identifier. |
| duration_usec | long | Duration usec. |
| egress_throttled_bytes | long | Egress throttled size in bytes. |
| egress_throttled_bytes_delta | long | Egress throttled size in bytes delta. |
| elapsed_since_renewal | long | Elapsed since renewal. |
| error_description | string | Error description. |
| error_response | string | Error response. |
| errorcode | string | Errorcode. |
| etag_value | string | Etag value. |
| event | string | Event name emitted by the component. |
| extra_params | string | Extra params. |
| fcb_volume_type | long | Type classification for fcb volume. |
| file_byte_count | long | Number of file byte. |
| file_byte_offset | long | File byte offset. |
| file_creation_status | bool | Boolean flag indicating whether file creation status. |
| file_handle | string | File handle. |
| file_path | string | File path. |
| file_path_hash | string | File path hash. |
| flags_attributes | long | Flags attributes. |
| found_leaked_handle | bool | Boolean flag indicating whether found leaked handle. |
| function_module | string | Function module. |
| handle_info | string | Handle info. |
| handle_leak_threshold_time_seconds | long | Handle leak threshold time seconds. |
| handle_list | string | Handle list. |
| has_agg_volume | bool | Boolean flag indicating whether has agg volume. |
| header | string | Header. |
| high_io_bucket_count | long | Number of high I/O bucket. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| http_call | string | Http call. |
| http_errorcode | long | Http errorcode. |
| http_response_code | long | Http response code. |
| inferred_tier | bool | Boolean flag indicating whether inferred tier. |
| ingress_throttled_bytes | long | Ingress throttled size in bytes. |
| ingress_throttled_bytes_delta | long | Ingress throttled size in bytes delta. |
| instance_rg_size | string | Instance resource governor size. |
| internet_status | long | Status value for internet. |
| io_count_threshold | long | I/O count threshold. |
| iops_bursting_eval_FS_Enabled | bool | Boolean flag indicating whether IOPS bursting eval FS Enabled. |
| iops_bursting_scaledown | bool | Boolean flag indicating whether IOPS bursting scaledown. |
| iops_bursting_scaleup | bool | Boolean flag indicating whether IOPS bursting scaleup. |
| iops_limit | long | IOPS limit. |
| iops_limit_delta | long | IOPS limit delta. |
| iops_throttled_request_count | long | Number of IOPS throttled request. |
| iops_throttled_request_count_delta | long | IOPS throttled request count delta. |
| is_block_blob | bool | Boolean flag indicating whether block blob. |
| is_for_log | bool | Boolean flag indicating whether for log. |
| is_for_write | bool | Boolean flag indicating whether for write. |
| is_read | bool | Boolean flag indicating whether read. |
| is_refresh_aad_token | bool | Boolean flag indicating whether refresh Azure AD token. |
| key_generation_date | string | Key generation date. |
| key_used | string | Key used. |
| last_error | long | Last error. |
| last_modified | string | Last modified. |
| latency_eval_FS_Enabled | bool | Boolean flag indicating whether latency eval FS Enabled. |
| latency_scaledown | bool | Boolean flag indicating whether latency scaledown. |
| latency_scaleup | bool | Boolean flag indicating whether latency scaleup. |
| latency_scaling_enabled | bool | Boolean flag indicating whether latency scaling enabled. |
| latency_scaling_use_avg | bool | Boolean flag indicating whether latency scaling use avg. |
| lease_action | string | Lease action. |
| lease_header_used | bool | Boolean flag indicating whether lease header used. |
| lease_order_id | string | Lease order identifier. |
| lease_state | string | State value for lease. |
| low_io_utilization_period | bool | Boolean flag indicating whether low I/O utilization period. |
| mapped_errorcode | long | Mapped errorcode. |
| marker_file_name | string | Marker file name. |
| max_bound_scaleup | bool | Boolean flag indicating whether max bound scaleup. |
| max_scaleups_after_scaledown_scaledown | bool | Boolean flag indicating whether max scaleups after scaledown scaledown. |
| message | string | Human-readable message text. |
| metadata_key | string | Metadata key. |
| metadata_marker_file_value | string | Metadata marker file value. |
| metadata_name | string | Metadata name. |
| metadata_sql_stored_value | string | Metadata SQL stored value. |
| metadata_validation_result | long | Metadata validation result. |
| metadata_value | string | Metadata value. |
| metdata_mismatch_type | long | Type classification for metdata mismatch. |
| min_bound_scaledown | bool | Boolean flag indicating whether min bound scaledown. |
| min_bound_scaleup | bool | Boolean flag indicating whether min bound scaleup. |
| min_num_eval_scaledown | bool | Boolean flag indicating whether min num eval scaledown. |
| minutes_as_primary | long | Minutes as primary. |
| new_app_instance_id | string | New app instance identifier. |
| new_lease_order_id | string | New lease order identifier. |
| num_bytes_read | long | Num size in bytes read. |
| num_bytes_to_read | long | Num size in bytes to read. |
| num_bytes_to_write | long | Num size in bytes to write. |
| num_bytes_written | long | Num size in bytes written. |
| number_of_active_winhttp_connections | long | Number of active winhttp connections. |
| number_of_active_winhttp_sessions | long | Number of active winhttp sessions. |
| old_app_instance_id | string | Old app instance identifier. |
| old_blob_lease_id | string | Old blob lease identifier. |
| old_lease_order_id | string | Old lease order identifier. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| page_blob_tier | string | Page blob tier. |
| percentage_high_threshold | long | Percentage high threshold. |
| period_ms | long | Period ms in milliseconds. |
| pfs_access_type | long | Type classification for pfs access. |
| pfs_scaling_context | string | Pfs scaling context. |
| pfs_scaling_params | string | Pfs scaling params. |
| pfs_scaling_signal_type | long | Type classification for pfs scaling signal. |
| point_of_interest | string | Point of interest. |
| primary_correlation_id | string | Primary correlation identifier. |
| queue_size | long | Queue size. |
| raw_data | string | Raw data. |
| request_context | string | Request context. |
| request_handle | string | Request handle. |
| request_id | string | Request identifier used to correlate the operation. |
| request_seq_num | long | Request seq num. |
| request_state_when_cancelled | string | Request state when cancelled. |
| request_str | string | Request str. |
| request_type | string | Type classification for request. |
| requested_byte_count | long | Number of requested byte. |
| resource | string | Resource. |
| response_receive_duration_usec | long | Response receive duration usec. |
| result_string | string | Result string. |
| retry_count | long | Number of retry. |
| retry_reason | string | Retry reason. |
| retry_wait_time_ms | long | Retry wait time ms in milliseconds. |
| rw_latency | long | Rw latency. |
| sequence_number | long | Sequence number. |
| server_file_handle_id | string | Server file handle identifier. |
| server_file_handle_open_time | string | Server file handle open time timestamp. |
| sessionName | string | Session Name. |
| session_id | long | Session identifier. |
| share_mode | long | Share mode. |
| share_snapshot_usage_bytes | long | Share snapshot usage size in bytes. |
| share_snapshot_usage_bytes_delta | long | Share snapshot usage size in bytes delta. |
| share_throttling_stats_reset | bool | Boolean flag indicating whether share throttling stats reset. |
| share_usage_bytes | long | Share usage size in bytes. |
| share_usage_bytes_delta | long | Share usage size in bytes delta. |
| size_eval_FS_Enabled | bool | Boolean flag indicating whether size eval FS Enabled. |
| size_scaledown | bool | Boolean flag indicating whether size scaledown. |
| size_scaleup | bool | Boolean flag indicating whether size scaleup. |
| smb_session_id | string | Smb session identifier. |
| ssl_errorcode | long | Ssl errorcode. |
| success_message | string | Success message. |
| template_file_exists | bool | Boolean flag indicating whether template file exists. |
| thread_id | long | Thread identifier. |
| throttling_eval_FS_Enabled | bool | Boolean flag indicating whether throttling eval FS Enabled. |
| throttling_record_start_time_utc | long | Throttling record start time utc. |
| throttling_scaledown | bool | Boolean flag indicating whether throttling scaledown. |
| throttling_scaleup | bool | Boolean flag indicating whether throttling scaleup. |
| time_elapsed_since_handle_open | long | Time elapsed since handle open. |
| total_egress_bytes | long | Total egress size in bytes. |
| total_egress_bytes_delta | long | Total egress size in bytes delta. |
| total_ingress_bytes | long | Total ingress size in bytes. |
| total_ingress_bytes_delta | long | Total ingress size in bytes delta. |
| total_io_count | long | Number of total I/O. |
| total_latency_us | long | Total latency us. |
| total_request_count | long | Number of total request. |
| total_request_count_delta | long | Total request count delta. |
| transferred_byte_count | long | Number of transferred byte. |
| updated_premium_remote_storage_volume_type | long | Type classification for updated premium remote storage volume. |
| value | string | Value. |
| volume_identity | string | Volume identity. |
| volume_name | string | Volume name. |
| volume_type | long | Type classification for volume. |
| wait_time_ms | long | Wait time in milliseconds. |
| win32_error_code | long | Win32 error code. |
| winhttp_call_type | string | Type classification for winhttp call. |
| winhttp_request_duration_usec | long | Winhttp request duration usec. |
| winhttp_timeout_count | long | Number of winhttp timeout. |
| xagent_signal_success | bool | Boolean flag indicating whether xagent signal success. |
| xstore_client_request_id | string | Xstore client request identifier. |
| xstore_cred | string | Xstore cred. |
| xstore_path_identifier | long | Xstore path identifier. |

## MonSQLXStoreIOStats — SQLXStore IOStats

**Purpose**: SQLXStore IOStats. Used to troubleshoot storage usage, persistence, I/O characteristics, and storage-engine side effects. Referenced in MI template areas: availability, backup-restore, performance. Often used during backup or restore investigations.
**Category**: Performance

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| attach_activity_id | string | Attach activity identifier. |
| attach_activity_id_xfer | string | Attach activity id xfer. |
| blob_count | long | Number of blob. |
| code_package_version | string | Code package version. |
| consecutive_no_error_intervals | long | Consecutive no error intervals. |
| consecutive_no_usage_intervals | long | Consecutive no usage intervals. |
| correlation_id | string | Correlation identifier used across components. |
| crc_calc_ms | long | Crc calc ms in milliseconds. |
| distributed_execution_id | string | Distributed execution identifier. |
| distributed_query_hash | string | Distributed query hash. |
| distributed_query_operator_id | string | Distributed query operator identifier. |
| distributed_request_id | string | Distributed request identifier. |
| distributed_scheduler_id | string | Distributed scheduler identifier. |
| distributed_statement_id | string | Distributed statement identifier. |
| distributed_step_index | string | Distributed step index. |
| distributed_submission_id | string | Distributed submission identifier. |
| distributed_task_group_id | string | Distributed task group identifier. |
| error_number | long | SQL or platform error number. |
| event | string | Event name emitted by the component. |
| file_path | string | File path. |
| file_path_hash | string | File path hash. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| inferred_tier | bool | Boolean flag indicating whether inferred tier. |
| interval_duration_milliseconds | long | Interval duration in milliseconds. |
| is_lock_error | bool | Boolean flag indicating whether lock error. |
| is_page_blob | bool | Boolean flag indicating whether page blob. |
| is_success | bool | Boolean flag indicating whether success. |
| latency_bucket_us | long | Latency bucket us. |
| latency_hits_00 | long | Latency hits 00. |
| latency_hits_01 | long | Latency hits 01. |
| latency_hits_02 | long | Latency hits 02. |
| latency_hits_03 | long | Latency hits 03. |
| latency_hits_04 | long | Latency hits 04. |
| latency_hits_05 | long | Latency hits 05. |
| latency_hits_06 | long | Latency hits 06. |
| latency_hits_07 | long | Latency hits 07. |
| latency_hits_08 | long | Latency hits 08. |
| latency_hits_09 | long | Latency hits 09. |
| latency_hits_10 | long | Latency hits 10. |
| latency_hits_11 | long | Latency hits 11. |
| latency_hits_12 | long | Latency hits 12. |
| latency_hits_13 | long | Latency hits 13. |
| latency_hits_14 | long | Latency hits 14. |
| latency_hits_15 | long | Latency hits 15. |
| latency_hits_total | long | Latency hits total. |
| max_bytes_per_read | long | Maximum size in bytes per read. |
| max_bytes_per_request | long | Maximum size in bytes per request. |
| max_bytes_per_write | long | Maximum size in bytes per write. |
| max_microsec_per_read | long | Maximum microsec per read. |
| max_microsec_per_request | long | Maximum microsec per request. |
| max_microsec_per_write | long | Maximum microsec per write. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| page_blob_tier | string | Page blob tier. |
| period_ms | long | Period ms in milliseconds. |
| request_type | string | Type classification for request. |
| sessionName | string | Session Name. |
| sleep_duration_microseconds | long | Sleep duration microseconds. |
| sleep_duration_milliseconds | long | Sleep duration in milliseconds. |
| storage_account | string | Storage account. |
| tier_change_timestamp | string | Tier change timestamp. |
| total_bytes | long | Total size in bytes. |
| total_microsec | long | Total microsec. |
| total_other_failed_reads | long | Total other failed reads. |
| total_other_failed_requests | long | Total other failed requests. |
| total_other_failed_writes | long | Total other failed writes. |
| total_outstanding_io | long | Total outstanding I/O. |
| total_read_bytes | long | Total read size in bytes. |
| total_read_bytes_failed | long | Total read size in bytes failed. |
| total_read_bytes_successful | long | Total read size in bytes successful. |
| total_read_microsec | long | Total read microsec. |
| total_read_requests_failed | long | Total read requests failed. |
| total_read_requests_successful | long | Total read requests successful. |
| total_reads | long | Total reads. |
| total_requested_bytes | long | Total requested size in bytes. |
| total_requested_read_bytes | long | Total requested read size in bytes. |
| total_requested_write_bytes | long | Total requested write size in bytes. |
| total_requests | long | Total requests. |
| total_retries | long | Total retries. |
| total_retry_wait_time_ms | long | Total retry wait time ms. |
| total_successful_microsec | long | Total successful microsec. |
| total_successful_read_microsec | long | Total successful read microsec. |
| total_successful_reads | long | Total successful reads. |
| total_successful_requests | long | Total successful requests. |
| total_successful_write_microsec | long | Total successful write microsec. |
| total_successful_writes | long | Total successful writes. |
| total_throttled_reads | long | Total throttled reads. |
| total_throttled_requests | long | Total throttled requests. |
| total_throttled_writes | long | Total throttled writes. |
| total_write_bytes | long | Total write size in bytes. |
| total_write_bytes_failed | long | Total write size in bytes failed. |
| total_write_bytes_successful | long | Total write size in bytes successful. |
| total_write_microsec | long | Total write microsec. |
| total_write_requests_failed | long | Total write requests failed. |
| total_write_requests_successful | long | Total write requests successful. |
| total_writes | long | Total writes. |
| total_xio_requests | long | Total xio requests. |

# 10. Other

## MonAuditOperational — Audit Operational

**Purpose**: Audit Operational. Used for specialized MI diagnostics that do not fit the primary troubleshooting buckets. Referenced in MI template areas: general. Often used when validating audit setup or audit runtime behavior.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| audit_guid | string | Audit guid. |
| audit_id | long | Audit identifier. |
| audit_name | string | Audit name. |
| code_package_version | string | Code package version. |
| database_id | long | Database identifier. |
| error | long | Error text captured for the event or operation. |
| error_code | long | Numeric error code for the failure or event. |
| event | string | Event name emitted by the component. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| is_geo_replica | bool | Boolean flag indicating whether geo replica. |
| is_named_replica | bool | Boolean flag indicating whether named replica. |
| logical_database_guid | string | Logical database guid. |
| logical_database_name | string | Logical database name. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| sessionName | string | Session Name. |
| state | long | Current lifecycle or health state. |
| target_path | string | Target path. |

## MonAuditOperationalTelemetry — Audit Operational Telemetry

**Purpose**: Audit Operational Telemetry. Used for specialized MI diagnostics that do not fit the primary troubleshooting buckets. Referenced in MI template areas: general. Often used when validating audit setup or audit runtime behavior.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| audit_action_groups_added | string | Audit action groups added. |
| audit_action_groups_dropped | string | Audit action groups dropped. |
| audit_guid | string | Audit guid. |
| audit_id | long | Audit identifier. |
| audit_name | string | Audit name. |
| audit_specification_name | string | Audit specification name. |
| category | string | Category. |
| code_package_version | string | Code package version. |
| database_id | long | Database identifier. |
| event | string | Event name emitted by the component. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| logical_database_guid | string | Logical database guid. |
| logical_database_name | string | Logical database name. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| retention_days | long | Retention days. |
| sessionName | string | Session Name. |
| state | bool | Current lifecycle or health state. |
| target_path | string | Target path. |

## MonAuditRuntimeTelemetry — Audit Runtime Telemetry

**Purpose**: Audit Runtime Telemetry. Used for specialized MI diagnostics that do not fit the primary troubleshooting buckets. Referenced in MI template areas: general. Often used when validating audit setup or audit runtime behavior.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| audit_guid | string | Audit guid. |
| audit_name | string | Audit name. |
| audit_target_session_enum | long | Audit target session enum. |
| audited_queries | long | Audited queries. |
| code_package_version | string | Code package version. |
| database_id | long | Database identifier. |
| dropped_events_count | long | Number of dropped events. |
| event | string | Event name emitted by the component. |
| failed_blob_writes | long | Failed blob writes. |
| fired_events_count | long | Number of fired events. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| is_local_secondary | bool | Boolean flag indicating whether local secondary. |
| logical_database_guid | string | Logical database guid. |
| logical_database_name | string | Logical database name. |
| managed_identity_cred | bool | Boolean flag indicating whether managed identity cred. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| sessionName | string | Session Name. |
| statement_avg_chars_len | long | Statement avg chars len. |
| statement_max_chars_len | long | Statement max chars len. |
| successful_blob_writes | long | Successful blob writes. |

## MonAuditSessionStatus — Audit Session Status

**Purpose**: Audit Session Status. Used for specialized MI diagnostics that do not fit the primary troubleshooting buckets. Referenced in MI template areas: general. Often used when validating audit setup or audit runtime behavior.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| audit_guid | string | Audit guid. |
| audit_id | long | Audit identifier. |
| audit_name | string | Audit name. |
| audit_scope_type | string | Type classification for audit scope. |
| code_package_version | string | Code package version. |
| database_id | long | Database identifier. |
| event | string | Event name emitted by the component. |
| file_path | string | File path. |
| hotpatch_data_package_version | string | Hotpatch data package version. |
| is_local_secondary | bool | Boolean flag indicating whether local secondary. |
| logical_database_guid | string | Logical database guid. |
| logical_database_name | string | Logical database name. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| sessionName | string | Session Name. |
| status | string | Current status reported by the component. |
| status_time | datetime | Status time timestamp. |

## MonDwBilling — billing warehouse Billing

**Purpose**: billing warehouse Billing. Used for specialized MI diagnostics that do not fit the primary troubleshooting buckets. Referenced in MI template areas: backup-restore, general. Often used for sizing or billing-related investigations. Often used during backup or restore investigations.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| billing_metric_name | string | Billing metric name. |
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| details_format | string | Details format. |
| error_type | string | Type classification for error. |
| event | string | Event name emitted by the component. |
| exception_details_format | string | Exception details format. |
| execution_time_msec | long | Execution time msec. |
| file_path | string | File path. |
| file_type | string | Type classification for file. |
| logical_database_id | string | Logical database identifier. |
| logical_database_name | string | Logical database name. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| physical_database_name | string | Physical database name. |
| process_id | long | Process identifier. |
| sessionName | string | Session Name. |
| size_in_bytes | real | Size in size in bytes. |
| storage_account_name | string | Storage account name. |
| storage_account_type | string | Type classification for storage account. |
| storage_container_name | string | Storage container name. |

## MonNonPiiAudit — Non Pii Audit

**Purpose**: Non Pii Audit. Used for specialized MI diagnostics that do not fit the primary troubleshooting buckets. Referenced in MI template areas: availability, backup-restore. Often used when validating audit setup or audit runtime behavior.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| authorized_roles | string | Authorized roles. |
| certificate_thumbprint | string | Certificate thumbprint. |
| code_package_version | string | Code package version. |
| collect_current_thread_id | long | Collect current thread identifier. |
| credential_type | long | Type classification for credential. |
| event | string | Event name emitted by the component. |
| event_code | long | Event code. |
| event_status | long | Status value for event. |
| incident_id | string | Incident identifier. |
| incident_store | string | Incident store. |
| message_systemmetadata | string | Message systemmetadata. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| parameters | string | Parameters. |
| presented_claims | string | Presented claims. |
| process_id | long | Process identifier. |
| request | string | Request. |
| request_action | string | Request action. |
| request_id | string | Request identifier used to correlate the operation. |
| request_method | string | Request method. |
| risk_classification_level | long | Risk classification level. |
| safety_attestation | long | Safety attestation. |
| service_owner | string | Service owner. |
| sessionName | string | Session Name. |
| time_created | datetime | Time created. |
| touch_category | long | Touch category. |
| touch_type | long | Type classification for touch. |
| user_agent | string | User agent. |
| username | string | Username. |

## MonSqlAgent — SQL Agent

**Purpose**: SQL Agent. Used for specialized MI diagnostics that do not fit the primary troubleshooting buckets. Referenced in MI template areas: availability, backup-restore.
**Category**: General

| Column | Type | Description |
|--------|------|-------------|
| AppName_Ex | string | App Name Ex. |
| AppTypeName_Ex | string | App Type Name Ex. |
| PartitionId | string | Partition Id. |
| event | string | Event name emitted by the component. |
| message | string | Human-readable message text. |
| message_type | string | Type classification for message. |
| originalEventTimestamp | datetime | Original Event timestamp. |
| package | string | Package. |
| resource_id | long | Resource identifier. |
| sessionName | string | Session Name. |

## MonManagedDatabaseInfo — Managed database metadata details

**Purpose**: Managed database metadata detail snapshot used by replication TSGs to validate collation and database identity on MI workers.
**Category**: Backup-restore / Replication
**Schema source**: `kusto_table_schema` on `sqlazureeas2follower.eastasia.kusto.windows.net`, database `sqlazure1`

| Column | Type | Description |
|--------|------|-------------|
| TIMESTAMP | datetime | Event timestamp. |
| PreciseTimeStamp | datetime | High precision event timestamp. |
| ClusterName | string | Cluster name. |
| NodeRole | string | Node role. |
| MachineName | string | Machine name. |
| NodeName | string | Node name. |
| AppName | string | Application name. |
| AppTypeName | string | Application type name. |
| LogicalServerName | string | Managed instance logical server name. |
| SubscriptionId | string | Customer subscription identifier. |
| ResourceGroup | string | Customer resource group. |
| code_package_version | string | SQL MI code package version. |
| end_utc_date | datetime | End of snapshot validity window. |
| start_utc_date | datetime | Start of snapshot validity window. |
| sql_database_id | long | SQL database ID. |
| managed_database_id | string | Managed database GUID. |
| owner_sid | string | Database owner SID. |
| compatibility_level | long | Database compatibility level. |
| collation_name | string | Database collation name. |
| SourceNamespace | string | Telemetry source namespace. |
| SourceMoniker | string | Telemetry source moniker. |
| SourceVersion | string | Telemetry source version. |
| __AuthType__ | string | Internal auth type. |
| __AuthIdentity__ | string | Internal auth identity. |
| polybase_enabled | string | PolyBase enabled flag. |
| PartitionId | string | Partition identifier. |
| allow_polybase_export | string | PolyBase export setting. |
| __IsTrusted__ | string | Internal trust marker. |

## AlrWinFabHealthDeployedAppEvent — Service Fabric deployed application health alerts

**Purpose**: Service Fabric deployed application health alert surface used by replication TSGs to confirm `sqlagent.exe` crash loops and other application exit faults.
**Category**: Availability / Replication
**Schema source**: `kusto_table_schema` on `sqlazureeas2follower.eastasia.kusto.windows.net`, database `sqlazure1`

| Column | Type | Description |
|--------|------|-------------|
| TIMESTAMP | datetime | Event timestamp. |
| PreciseTimeStamp | datetime | High precision event timestamp. |
| ClusterName | string | Cluster name. |
| NodeRole | string | Node role. |
| MachineName | string | Machine name. |
| NodeName | string | Node name. |
| AppName | string | Application name. |
| AppTypeName | string | Application type name. |
| LogicalServerName | string | Managed instance logical server name. |
| SubscriptionId | string | Customer subscription identifier. |
| ResourceGroup | string | Customer resource group. |
| ApplicationName | string | Service Fabric deployed application name. |
| HealthState | string | Health state classification. |
| SourceId | string | Health source identifier. |
| Property | string | Health property name. |
| Description | string | Health event description. |
| IsExpired | bool | Expiration flag for the health event. |
| Version | long | Health event version. |
| NodeEntityName | string | Node entity name. |
| SourceNamespace | string | Telemetry source namespace. |
| SourceMoniker | string | Telemetry source moniker. |
| SourceVersion | string | Telemetry source version. |
| __AuthType__ | string | Internal auth type. |
| __AuthIdentity__ | string | Internal auth identity. |
| OneBoxClusterId | string | OneBox cluster identifier. |
| ClusterEntityName | string | Cluster entity name. |
| __IsTrusted__ | string | Internal trust marker. |

# MI Filter Patterns

```kql
// Scope to Managed Instance worker workloads
| where AppTypeName startswith "Worker.CL"

// Filter by MI server name (column name varies by table)
| where LogicalServerName =~ "{ServerName}"
| where logical_server_name =~ "{ServerName}"
| where server_name =~ "{ServerName}"
| where name =~ "{ServerName}"

// Filter by database name (column name varies by table)
| where logical_database_name =~ "{DatabaseName}"
| where database_name =~ "{DatabaseName}"
| where managed_database_name =~ "{DatabaseName}"

// Time filters
| where TIMESTAMP between (ago(1h) .. now())
| where PreciseTimeStamp between (datetime(2026-01-01) .. datetime(2026-01-02))
| where originalEventTimestamp >= datetime(2026-01-01 00:00:00Z)

// Common correlation filters
| where request_id == "{RequestId}"
| where correlation_id == "{CorrelationId}"
| where operation_id == "{OperationId}"
```

# Skipped / Not Found Tables

The following requested tables did not return schema rows from the target cluster/database and were skipped:

- MonAdoDeploymentCabSnapshot
- MonAzureActiveDirService
- MonBackupFull
- MonCvBranchBuildVersionMetadata
- MonDmOsBPoolPerfCountersBuffer
- MonDmOsWaitstats
- MonMIGeoDRFailoverGroupsConnectivity
- MonManagedInstanceSSBConversations
- MonRolloutFiltered
- MonSQLXStoreBlocking
- MonWatsonAnalysis
- MonWatsonCloudTestAnalysis
