using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;

public class TaskManager : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI startText;
    [SerializeField] private GameObject startPanel;
    [SerializeField] private Task1 task1;

    public int currentTask = 0;

    private void Start()
    {
        startPanel.SetActive(true);
        task1.Hide();
    }

    public void StartNextTask()
    {
        currentTask++;
        Debug.Log("Starting task: " + currentTask);

        if (currentTask == 1)
        {
            StartCoroutine(Do321_count());
        }
    }

    private IEnumerator Do321_count()
    {
        startPanel.SetActive(true);
        startText.gameObject.SetActive(true);

        string[] countdown = { "3", "2", "1", "Go!" };

        foreach (string count in countdown)
        {
            startText.text = count;
            yield return new WaitForSeconds(1f);
        }

        startText.gameObject.SetActive(false);
        startPanel.SetActive(false);

        task1.Show();
        task1.StartTask();
    }

    public void IntermediatePanel()
    {

        startPanel.SetActive(true);
        startText.gameObject.SetActive(true);
        startText.text = currentTask + "/6 tasks completed.\n Wait for the next task.";

    }
}
