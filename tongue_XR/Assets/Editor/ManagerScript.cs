using UnityEditor;
using UnityEngine;

[CustomEditor(typeof(TaskManager))]
public class ManagerScript : Editor
{
    public override void OnInspectorGUI()
    {
        DrawDefaultInspector(); // Draw the default inspector

        TaskManager controller = (TaskManager)target;

        GUILayout.Space(10);
        GUILayout.Label("User Testing Controls", EditorStyles.boldLabel);

        if (GUILayout.Button("Start Next Task"))
        {
            controller.StartNextTask();
        }
    }
}
